import cv2
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QPoint, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPainter
from decisionlabeling.models import StateListener, FrameMode, LabelTracker
from decisionlabeling.utils import draw_detection
from decisionlabeling.models import KeyboardListener
from decisionlabeling.models.polygon import Bbox, Polygon
from decisionlabeling.config import DATA_DIR
from decisionlabeling.models.track_info import Detection
from decisionlabeling.styles import Theme
import numpy as np
import math
import time
from decisionlabeling import utils


class Event:
    DRAWING = "drawing"
    RESIZING = "resizing"
    DRAGGING = "dragging"
    MOVING = "moving"
    KEYPOINT_DRAGGING = "keypoint_dragging"


class Anchor:
    def __init__(self, anchor_key, anchor, detection_index):
        self.anchor_key = anchor_key
        self.anchor = anchor
        self.detection_index = detection_index

    def __repr__(self):
        return "Anchor({})".format(self.anchor)

class ImageWidget(QWidget, StateListener, KeyboardListener):
    signal = pyqtSignal()

    def __init__(self, state):
        super().__init__()

        self.img_scale = 0
        self.state = state
        self.state.add_listener(self)

        self.MIN_ZOOM, self.MAX_ZOOM = 0.9, 8.0
        self.zoom = 1.0
        self.offset = QPoint(0., 0.)
        self.original_img = None
        self.img = None

        # self.anchors_quadtree = None
        # self.detections_quadtree = None
        # self.keypoints_quadtree = None

        self.current_event = None
        self.current_detection = None
        self.current_anchor_key = None
        self.cursor_offset = None
        self.holding_ctrl = False

        self.setFixedSize(900, 900)
        self.setMouseTracking(True)

        self.current_frame = None
        self.current_video = None

        self.thickness = 2
        self.font = cv2.QT_FONT_NORMAL
        self.fontScale = 3
        self.betweenTextFontScale = 1

        self.side_color_dict = {'left':(178, 34, 34), 'right':(50,205,50),
                                None:(0, 0, 0), 0:(0, 0, 0)}
        self.side_axis_dict = {'left':(100, 600), 'right': (550, 600), None: (0, 0)}

        self.on_current_frame_change()
        self.label_tracker = LabelTracker(self.state)

    def get_visible_area(self):
        h, w, _ = self.img.shape
        zoom = self.zoom * self.img_scale

        offset_x = min(max(-self.offset.x() / zoom, 0), w)
        offset_y = min(max(-self.offset.y() / zoom, 0), h)

        screen_offset_x = max(self.offset.x() / zoom, 0)
        screen_offset_y = max(self.offset.y() / zoom, 0)

        width = min(self.width() / zoom - screen_offset_x, w - offset_x)
        height = min(self.height() / zoom - screen_offset_y, h - offset_y)

        return offset_x, offset_y, width, height

    def on_current_frame_change(self):
        # self.state.drawing = True

        start_time = time.time()

        is_different_img = self.current_frame != self.state.current_frame or self.current_video != self.state.current_video
        # if self.state.is_view_play and self.current_frame==self.state.nb_frames-350:
        #     blank_img = cv2.imread(DATA_DIR + 'blank.png')
        #     # for m in range(60):
        #     #     # blank_img = cv2.cvtColor(blank_img, cv2.COLOR_BGR2RGB)
        #
        #     cv2.putText(blank_img, "click play", (480,300),
        #                 self.font, self.fontScale, (0,0,0),
        #                 self.thickness, cv2.LINE_AA, False)
        #     # self.draw_bboxes(blank_img)
        #     #self.draw_image(blank_img)
        #     self.current_frame+=1

        if is_different_img:
            self.current_frame = self.state.current_frame
            self.current_video = self.state.current_video

            image_file = self.state.file_names[self.state.current_frame]
            img = cv2.imread(image_file)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            h, w, _ = img.shape
            self.img_scale = float(self.width()) / float(w)
            self.original_img = img.copy()
        else:
            img = self.original_img.copy()
            h, w, _ = img.shape = img.shape

        self.state.image_size = (h, w)

        # self.draw_bboxes(img)
        self.draw_stored_area(img)
        self.draw_masked_area(img)
        if not self.state.is_view_play and self.state.is_tag_play:
            self.draw_travel_path(img)
        if self.state.is_view_play and self.current_frame == self.state.nb_frames - 1:
            cv2.rectangle(img, (-50,0), (1024,768), (0,0,0), thickness=-1)
            cv2.putText(img, "press t to tag the video", (380, 370),
                                        self.font, self.betweenTextFontScale, (255, 255, 255),
                                        2, cv2.LINE_AA, False)
        if self.state.is_view_play and self.current_frame == 0 and not self.state.is_tag_play and \
                self.state.frame_mode == FrameMode.MANUAL:
            cv2.rectangle(img, (-50,0), (1024,768), (0,0,0), thickness=-1)
            cv2.putText(img, "press play to watch the video", (380, 370),
                                        self.font, self.betweenTextFontScale, (255, 255, 255),
                                        2, cv2.LINE_AA, False)
        self.draw_image(img)


    def on_frame_mode_change(self):
        if self.state.frame_mode == FrameMode.MANUAL:
            # self.update_quadtrees()
            pass

    def on_detection_change(self):
        self.on_current_frame_change()

    def on_theme_change(self):
        self.update_zoom_offset()

    def on_video_change(self):
        self.state.is_view_play = True
        self.state.is_tag_play = False
        self.state.frame_mode = FrameMode.MANUAL
        # self.
        self.on_current_frame_change()

    def draw_image(self, img):
        self.img_temp = img
        self.img = img

        self.update_zoom_offset()

    def draw_stored_area(self, img):
        if self.state.use_cropping_area:
            x_crop, y_crop, w_crop, h_crop = self.state.stored_area
            bbox = Bbox(*self.state.stored_area)
            H, W = self.state.image_size

            # Number of repeated cropping areas to span the entire image
            n_left = math.ceil(x_crop / w_crop)
            n_right = math.ceil((W - (x_crop + w_crop)) / w_crop)
            n_top = math.ceil(y_crop / h_crop)
            n_bottom = math.ceil((H - (y_crop + h_crop)) / h_crop)

            for i in range(-n_top, 1 + n_bottom):
                for j in range(-n_left, 1 + n_right):
                    pos_offset = bbox.pos.copy()
                    pos_offset += [j * w_crop, i * h_crop]
                    top_left, bottom_right = tuple(pos_offset.astype(int)), tuple((pos_offset + bbox.size).astype(int))
                    cv2.rectangle(img, top_left, bottom_right, color=(255, 0, 0), thickness=5)

    def draw_masked_area(self, img):
        # self.left_bbox = (125.0, 50.0, 80.0, 100.0)
        # self.right_bbox = Bbox(436.0, 16.0, 70.0, 90.0)
        cv2.rectangle(img, (120, 40), (220, 150), color=(178,34,34), thickness=-1)
        cv2.rectangle(img, (436, 10), (516, 106), color=(50,205,50), thickness=-1)
        if self.state.side != None:
            cv2.putText(img, self.state.side, self.side_axis_dict[self.state.side],
                        self.font, self.fontScale, self.side_color_dict[self.state.side],
                        self.thickness, cv2.LINE_AA, False)

    def draw_travel_path(self, img):
        self.label_tracker = LabelTracker(self.state)
        try:
            tagged_side = list(self.state.track_info.tagged_frames.keys())[-1]
        except IndexError:
            tagged_side = self.state.nb_frames+1
        colors =[]
        for i in range(self.state.current_frame + 1):
            if i < tagged_side and i < self.state.track_info.last_tagged_side:
                colors.append(self.side_color_dict[0])
            elif i < tagged_side and i <= self.state.track_info.last_tagged_side <= tagged_side:
                colors.append(self.side_color_dict[0])
            elif i < tagged_side and self.state.track_info.last_tagged_side<0:
                colors.append(self.side_color_dict[0])
            elif tagged_side > i >= self.state.track_info.last_tagged_side >= 0:
                side = self.state.track_info.tagged_frames[self.state.track_info.last_tagged_side]
                colors.append(self.side_color_dict[side])
            else:
                colors.append(self.side_color_dict[self.state.side])

        # colors = [self.side_color_dict[0] if i<tagged_side else self.side_color_dict[self.state.side]
        #           for i in range(self.state.current_frame+1)]


        if self.state.current_frame <= self.label_tracker.get_total_labelled_frames():
            for frame in range(self.state.current_frame+1):

                x_coord, y_coord = self.label_tracker.get_coords(frame)
                cv2.circle(img, (x_coord, y_coord), 4, colors[frame], -1)

    def update_zoom_offset(self):
        M = np.float32([[self.zoom * self.img_scale, 0, self.offset.x()],
                        [0, self.zoom * self.img_scale, self.offset.y()]])
        self.canvas = cv2.warpAffine(self.img, M, (900, 900), borderValue=Theme.get_image_bg(self.state.theme))

        self.state.visible_area = self.get_visible_area()

        self.signal.emit()  # update() is called in main thread

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.canvas is not None:
            height, width, bpc = self.canvas.shape
            bpl = bpc * width
            img = QImage(self.canvas.data, width, height, bpl, QImage.Format_RGB888)
            qp.drawImage(QPoint(0, 0), img)
        qp.end()

        # self.state.drawing = False

    def get_abs_pos(self, pos):
        return (pos - self.offset) / (self.zoom * self.img_scale)

    def on_key_ctrl(self, holding):
        self.holding_ctrl = holding

    def wheelEvent(self, event):
        pos = event.pos()
        old_p = (pos - self.offset) / self.zoom

        numPixels = event.pixelDelta().y()
        self.zoom = max(min(self.zoom + numPixels / 40, self.MAX_ZOOM), self.MIN_ZOOM)

        new_p = old_p * self.zoom + self.offset
        self.offset += pos - new_p

        self.update_zoom_offset()