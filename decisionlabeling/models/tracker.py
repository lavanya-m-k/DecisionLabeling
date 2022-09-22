import os
import torch
from .polygon import Polygon, Bbox
import json
import socket
import pickle
import cv2
import struct
from decisionlabeling.config import RESOURCES_DIR


class Tracker:
    def __init__(self, state):
        self.state = state
        # self.use_cuda = torch.cuda.is_available()
        # self.device = torch.device('cuda' if self.use_cuda else 'cpu')
        # torch.backends.cudnn.benchmark = True

    def init(self, img, bbox):
        """
        Arguments:
            img (OpenCV image): obtained from cv2.imread(img_file)
            bbox (BBox)
        """
        raise NotImplementedError

    def track(self, img):
        """
        Output:
            bbox (BBox), polygon (Polygon)
        """
        raise NotImplementedError

    def terminate(self):
        pass


class SocketTracker(Tracker):
    HOST = "128.178.17.112"
    PORT = 8787
    OK_SIGNAL, TERMINATE_SIGNAL = b"ok", b"terminate"

    def __init__(self, port=PORT):
        self.port = port

    def init(self, image_path, bbox):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.HOST, self.port))
        self.receive_ok_signal()

        self.send_bbox(bbox)
        self.send_image_path(image_path)

        res = self.receive_ok_signal()
        if res != self.OK_SIGNAL:
            raise Exception(res.decode())

    def track(self, image_path):
        self.send_image_path(image_path)
        data = self.receive_detection()

        if "error" in data:
            raise Exception(data["error"])

        return Bbox(*data["bbox"]), Polygon(data["polygon"])

    def send_image_path(self, image_path):
        data = image_path.encode()
        self.client_socket.sendall(data)

    def send_bbox(self, bbox):
        data = pickle.dumps(bbox.to_json())
        self.client_socket.send(data)

    def receive_detection(self):
        json_response = self.client_socket.recv(1024)
        response = json.loads(json_response.decode())
        return response

    def receive_ok_signal(self):
        data = self.client_socket.recv(1024)
        return data

    def send_terminate_signal(self):
        self.client_socket.sendall(self.TERMINATE_SIGNAL)

    def terminate(self):
        self.send_terminate_signal()
        self.client_socket.close()


class KCFTracker(Tracker):
    def __init__(self, state, **kwargs):
        super().__init__(**kwargs)
        self.state = state

    def init(self, image_path, bbox):
        img = cv2.imread(image_path)
        self.tracker = cv2.TrackerKCF_create()
        self.tracker.init(img, tuple(bbox.to_json()))
        self.tracker.update(img)

    def track(self, image_path):
        img = cv2.imread(image_path)
        success, bbox = self.tracker.update(img)

        if not success:
            return None, None

        bbox = Bbox(*bbox)
        return bbox, Polygon.from_bbox(bbox)
