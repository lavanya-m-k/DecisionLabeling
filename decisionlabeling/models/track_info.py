import json
import os
import pandas as pd
import numpy as np
import time
from .polygon import Polygon, Bbox, Keypoints
from decisionlabeling.class_names import DEFAULT_CLASS_NAMES
from decisionlabeling.config import OUTPUT_DIR, COLUMN_NAMES
from tqdm import tqdm
from collections import OrderedDict

class Detection:
    def __init__(self, class_id='unset', track_id=0, polygon=Polygon(), bbox=Bbox(),
                 keypoints=Keypoints(), tagged_frame=0, total_frames=100):
        self.class_id = class_id
        self.track_id = track_id
        self.polygon = polygon
        self.bbox = bbox
        self.keypoints = keypoints
        self.tagged_frame = tagged_frame
        self.total_frames = total_frames
        # self.user_name = user_name

    @staticmethod
    def from_json(data):
        return Detection(data["class_id"], data["track_id"],
                         Polygon(data["polygon"]), Bbox(*data["bbox"]),
                         Keypoints(data["keypoints"]), data["tagged_frame"],
                         data["total_frames"])

    def to_json(self):
        return {
            "track_id": self.track_id,
            "class_id": self.class_id,
            "polygon": self.polygon.to_json(),
            "bbox": self.bbox.to_json(),
            "keypoints": self.keypoints.to_json(),
            "tagged_frame": self.tagged_frame,
            "total_frames": self.total_frames
        }

    def to_dict(self):
        return {"track_id": self.track_id, "class_id": self.class_id, **self.bbox.to_dict(),
                "polygon": self.polygon.to_str(), "kp": self.keypoints.to_str(), "tagged_frame": self.tagged_frame,
                "total_frames": self.total_frames}

    @staticmethod
    def from_df(row):
        bbox = Bbox(row.x, row.y, row.w, row.h)
        return Detection(row.class_id, row.track_id,
                         Polygon.from_str(row.polygon), bbox,
                         Keypoints.from_str(row.kp), row.tagged_frame, row.total_frames)

    def copy(self):
        return Detection(self.class_id, self.track_id, self.polygon.copy(),
                         self.bbox.copy(), self.keypoints.copy(), self.tagged_frame,
                         self.total_frames)

    def __repr__(self):
        return "Detection(class_id={}, track_id={}, bbox={}, polygon={}, keypoints={})".format(self.class_id,
                                                                                               self.track_id,
                                                                                               self.bbox, self.polygon,
                                                                                               self.keypoints,
                                                                                               self.tagged_frame,
                                                                                               self.total_frames)


class TrackInfo:
    def __init__(self, video_name="", user_name=""):
        self.video_name = video_name

        self.nb_track_ids = 0
        self.class_names = DEFAULT_CLASS_NAMES
        self.user_name = user_name
        self.load_info()

        self.file_name = None
        self.detections = []
        self.tagged_frames = OrderedDict()
        self.last_tagged_side = -1
        self.total_frames = None

        dir_name = os.path.join(OUTPUT_DIR, self.user_name)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)




    def save_to_disk(self):
        self.write_info()
        # self.write_detections(self.file_name)

    def load_info(self):
        json_file = os.path.join(OUTPUT_DIR, self.video_name + "_info.json")
        # json_file = os.path.join(OUTPUT_DIR, "{}/info.json".format(self.video_name))

        if not os.path.exists(json_file):
            return

        with open(json_file, "r") as f:
            data = json.load(f)
            self.nb_track_ids = data["nb_track_ids"]
            if  data["user_name"]!=None:
                self.user_name = data["user_name"]
            #self.class_names = {int(k): v for k, v in json.loads(data["class_names"]).items()}

    @staticmethod
    def df_from_csv(file_name):
        if not os.path.exists(file_name):
            return pd.DataFrame(
                columns=COLUMN_NAMES)

        return pd.read_csv(file_name, header=None, names=COLUMN_NAMES,
                           na_filter=False, sep=" ")

    @staticmethod
    def df_to_csv(df, file_name):
        df.to_csv(file_name, index=None, header=False, sep=" ")

    @staticmethod
    def df_add_detection(df, detection: Detection):
        return df.append(detection.to_dict(), ignore_index=True)

    def to_df(self, file_names):
        df = pd.DataFrame(columns=COLUMN_NAMES)

        for i, file_name in enumerate(file_names):
            txt_file = os.path.join(OUTPUT_DIR, "{}/{}.txt".format(self.video_name, file_name))
            if not os.path.exists(txt_file):
                continue

            df_frame = self.df_from_csv(txt_file)
            df_frame["frame"] = i
            df_frame["xc"] = df_frame["x"] + df_frame["w"] / 2
            df_frame["yc"] = df_frame["y"] + df_frame["h"] / 2
            df_frame["infer"] = 0

            df_frame = df_frame[COLUMN_NAMES]
            df = df.append(df_frame, ignore_index=True)
        return df

    def from_df_all(self, df, file_names):
        df["x"] = df.xc - df.w / 2
        df["y"] = df.yc - df.h / 2

        df[["class_id", "track_id"]] = df[["class_id", "track_id"]].astype(int)
        df[["x", "y", "w", "h"]] = df[["x", "y", "w", "h"]].astype(float)

        for i, file_name in enumerate(file_names):
            txt_file = os.path.join(OUTPUT_DIR + "/" + self.user_name, "{}/{}.txt".format(self.video_name, file_name))

            df_frame = df[df.frame == i]
            df_frame = df_frame[["track_id", "class_id", "x", "y", "w", "h", "polygon", "kp"]]
            self.df_to_csv(df_frame, txt_file)

        # Update current detections
        self.detections = self.get_detections(self.file_name)

    def write_from_df(self, df, file_name):
        txt_file = os.path.join(OUTPUT_DIR + "/" + self.user_name, "{}/{}.txt".format(self.video_name, file_name))
        self.df_to_csv(df, txt_file)

        # Update current detections
        if file_name == self.file_name:
            self.detections = self.get_detections(self.file_name)

    def get_detections(self, file_name):
        txt_file = os.path.join(OUTPUT_DIR + "/" + self.user_name, "{}/{}.txt".format(self.video_name, file_name))

        if not os.path.exists(txt_file):
            return []

        df = self.df_from_csv(txt_file)
        return [Detection.from_df(row) for _, row in df.iterrows()]

    def load_detections(self, file_name):
        self.file_name = file_name
        self.detections = self.get_detections(file_name)

    def write_info(self):
        json_file = os.path.join(OUTPUT_DIR + "/" + self.user_name, self.video_name + "_info.json")
        # json_file = os.path.join(OUTPUT_DIR + "/" + self.user_name, "{}/info.json".format(self.video_name))

        data = {
            "video_name": self.video_name,
            "nb_track_ids": self.nb_track_ids,
            "user_name": self.user_name,
            "tagged_frames": self.tagged_frames,
            "total_frames": self.total_frames
        }

        if os.path.exists(json_file):
            with open(json_file, "r") as f:
                try:
                    existing_data = json.loads(f.read())
                    existing_data.update(data)
                    data = existing_data
                except json.decoder.JSONDecodeError:
                    print(f.read())

        with open(json_file, "w") as f:
            json.dump(data, f)
            f.write('\n')

    def write_detections(self, file_name, detections=None):
        txt_file = os.path.join(OUTPUT_DIR + "/" + self.user_name, "{}/{}.txt".format(self.video_name, file_name))

        if detections is None:
            detections = self.detections

        if file_name == self.file_name:
            self.detections = detections

        df = pd.DataFrame(columns=COLUMN_NAMES)
        if len(detections) > 0:
            df = df.append([d.to_dict() for d in detections], ignore_index=True)
        self.df_to_csv(df, txt_file)

        self.nb_track_ids = max(self.nb_track_ids, max([d.track_id for d in detections] or [0]) + 1)

    def add_detection(self, detection: Detection, file_name=None):
        if file_name is None or file_name == self.file_name:
            self.detections.append(detection)
        else:
            txt_file = os.path.join(OUTPUT_DIR + "/" + self.user_name, "{}/{}.txt".format(self.video_name, file_name))
            track_id = detection.track_id

            df = self.df_from_csv(txt_file)
            count = (df.track_id == track_id).sum()
            if count > 0:
                df[df.track_id == track_id] = detection.to_dict().values()
                self.df_to_csv(df, txt_file)
            else:
                self.df_to_csv(self.df_add_detection(df, detection), txt_file)

        self.nb_track_ids = max(self.nb_track_ids, detection.track_id + 1)

    def remove_detection(self, track_id, file_name):
        """
        Removes detections with specific track_id from detections file
        Returns true if at least one detection was deleted
        """
        if file_name == self.file_name:
            self.detections = [d for d in self.detections if d.track_id != track_id]
            return True

        txt_file = os.path.join(OUTPUT_DIR + "/" + self.user_name, "{}/{}.txt".format(self.video_name, file_name))

        if not os.path.exists(txt_file):
            return False

        df = self.df_from_csv(txt_file)

        count = (df.track_id == track_id).sum()
        if count == 0:
            return False

        self.df_to_csv(df[df.track_id != track_id], txt_file)
        return True

    def get_min_available_track_id(self):
        return self.nb_track_ids

    def modify_class_id(self, track_id, class_id, file_name):
        """
        Modifies class id with specific track_id from detections file
        Returns true if at least one modification was done
        """

        if file_name == self.file_name:
            for d in self.detections:
                if d.track_id == track_id:
                    d.class_id = class_id
            return True

        txt_file = os.path.join(OUTPUT_DIR + "/" + self.user_name, "{}/{}.txt".format(self.video_name, file_name))

        if not os.path.exists(txt_file):
            return False

        df = self.df_from_csv(txt_file)

        count = (df.track_id == track_id).sum()
        if count == 0:
            return False

        df.loc[df.track_id == track_id, "class_id"] = class_id

        self.df_to_csv(df, txt_file)
        return True
