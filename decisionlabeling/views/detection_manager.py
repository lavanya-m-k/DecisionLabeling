import os
import datetime
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QMessageBox, QCheckBox, QComboBox, QFormLayout, QLabel, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
from decisionlabeling.models import FrameMode, TrackInfo
from decisionlabeling.models.detector import SocketDetector
from decisionlabeling.models.polygon import Bbox
from decisionlabeling.config import DATA_DIR


class DetectionManager(QGroupBox):
    def __init__(self, state, ssh_login):
        super().__init__("Detection")

        self.state = state
        self.ssh_login = ssh_login

        self.detector = SocketDetector()
        options_layout = QFormLayout()

        crop_layout = QHBoxLayout()
        self.crop_checkbox = QCheckBox("Use cropping area", self)
        self.crop_checkbox.setChecked(self.state.use_cropping_area)
        self.crop_checkbox.stateChanged.connect(self.checked_cropping_area)
        self.crop_button = QPushButton("Choose cropping area")
        self.crop_button.clicked.connect(self.save_cropping_area)
        crop_layout.addWidget(self.crop_checkbox)
        crop_layout.addWidget(self.crop_button)
        options_layout.addRow(crop_layout)

        self.detached_checkbox = QCheckBox("Detached mode (for videos)", self)
        options_layout.addRow(self.detached_checkbox)

        self.fetch_info_button = QPushButton("Fetch detached info")
        self.fetch_info_button.clicked.connect(self.fetch_detached_info)
        options_layout.addRow(self.fetch_info_button)

        self.load_detached_detections_button = QPushButton("Load detached detections")
        self.load_detached_detections_button.clicked.connect(self.load_detached_detections)
        options_layout.addRow(self.load_detached_detections_button)

        self.detector_dropdown = QComboBox()
        self.detector_dropdown.addItems(["YOLO", "OpenPifPaf"])
        options_layout.addRow(QLabel("Detection net:"), self.detector_dropdown)

        self.frame_detection_thread = DetectionThread(self.state, self.detector, self, detect_video=False)
        self.frame_detection_thread.err_signal.connect(self.display_err_message)
        self.frame_detection_thread.finished.connect(self.on_detection_finished)

        self.detection_thread = DetectionThread(self.state, self.detector, self, detect_video=True)
        self.detection_thread.err_signal.connect(self.display_err_message)
        self.detection_thread.finished.connect(self.on_detection_finished)

        run_layout = QHBoxLayout()
        self.frame_detection_button = QPushButton("Run on frame")
        self.frame_detection_button.clicked.connect(self.on_frame_detection_clicked)

        self.detection_button = QPushButton("Run on video")
        self.detection_button.clicked.connect(self.on_detection_clicked)

        run_layout.addWidget(self.frame_detection_button)
        run_layout.addWidget(self.detection_button)

        layout = QVBoxLayout()
        layout.addLayout(options_layout)
        layout.addLayout(run_layout)
        self.setLayout(layout)

    def display_err_message(self, err_message):
        QMessageBox.warning(self, "", "Error: {}".format(err_message))

    def on_frame_detection_clicked(self):
        if not self.state.detection_server_running:
            QMessageBox.warning(self, "", "Detection server is not connected.")
            return

        self.detection_button.setEnabled(False)
        self.frame_detection_button.setEnabled(False)

        self.frame_detection_thread.start()

    def on_detection_clicked(self):
        if not self.state.detection_server_running:
            QMessageBox.warning(self, "", "Detection server is not connected.")
            return

        if self.detached_checkbox.isChecked():
            if self._is_detached_running():
                qm = QMessageBox
                res = qm.question(self, "", "Are you sure you want to start a new detached detection. This will kill the currently running one", qm.Yes | qm.No)

                if res == qm.No:
                    return

        self.detection_button.setEnabled(False)
        self.frame_detection_button.setEnabled(False)

        self.detection_thread.start()

    def on_detection_finished(self):
        self.detection_button.setEnabled(True)
        self.frame_detection_button.setEnabled(True)

    def fetch_detached_info(self):
        if not self.state.detection_server_running:
            QMessageBox.warning(self, "", "Detection server is not connected.")
            return

        info = self.ssh_login.fetch_detached_info()
        if info is None:
            QMessageBox.warning(self, "", "Information file not found on the server.")
            return

        if "error" in info:
            QMessageBox.warning(self, "", "An error occurred in the detached session: {}".format(info["error"]))
            return

        message = "Video: {}\nFrame: {}/{}\nStart time: {}\nLast update: {}".format(info["video_name"], info["current_frame"], info["total_frame"], info["start_time"], info["last_update"])
        QMessageBox.information(self, "", message)

    def _is_detached_running(self):
        info = self.ssh_login.fetch_detached_info()

        if not info:
            return False

        last_update = datetime.datetime.strptime(info["last_update"], "%Y-%m-%d %H:%M:%S.%f")
        now = datetime.datetime.now()

        return (now - last_update).total_seconds() < 60

    def load_detached_detections(self):
        if not self.state.detection_server_running:
            QMessageBox.warning(self, "", "Detection server is not connected.")
            return

        self.ssh_login.load_detached_detections(self.state.current_video)  # TODO: WARNING this will overwrite current annotations

        self.state.track_info = TrackInfo(self.state.current_video)
        self.state.track_info.load_detections(self.state.get_file_name())

        self.state.notify_listeners("on_detection_change")

    def checked_cropping_area(self):
        if self.crop_checkbox.isChecked():
            self.state.use_cropping_area = True

            if self.state.stored_area == (0, 0, 0, 0):
                self.state.stored_area = self.state.visible_area
        else:
            self.state.use_cropping_area = False

        self.state.notify_listeners("on_current_frame_change")

    def save_cropping_area(self):
        self.crop_checkbox.setChecked(True)
        self.state.stored_area = self.state.visible_area
        self.state.notify_listeners("on_current_frame_change")


class DetectionThread(QThread):
    err_signal = pyqtSignal(str)

    def __init__(self, state, detector, parent, detect_video=True):
        super().__init__()
        self.state = state
        self.detector = detector
        self.detect_video = detect_video
        self.parent = parent

    def run(self):
        self.detector.init()

        crop_area = None
        if self.parent.crop_checkbox.isChecked():
            crop_area = Bbox(*self.state.stored_area)

        detached = self.parent.detached_checkbox.isChecked()

        detector = str(self.parent.detector_dropdown.currentText())

        if self.detect_video:
            seq_path = os.path.join(DATA_DIR, self.state.current_video)

            if not detached:

                self.state.frame_mode = FrameMode.CONTROLLED

                try:
                    for frame, detections in enumerate(self.detector.detect_sequence(seq_path, self.state.nb_frames, crop_area=crop_area, detector=detector)):
                        self.state.set_detections(detections, frame)

                        if self.state.frame_mode == FrameMode.CONTROLLED or self.state.current_frame == frame:
                            self.state.set_current_frame(frame)
                except Exception as e:
                    self.err_signal.emit(str(e))
                    self.detector.terminate()

                self.state.frame_mode = FrameMode.MANUAL

            else:

                self.parent.ssh_login.start_detached_detection(seq_path, crop_area=crop_area, detector=detector)

        else:
            image_path = self.state.file_names[self.state.current_frame]

            try:
                detections = self.detector.detect(image_path, crop_area=crop_area, detector=detector)
                self.state.set_detections(detections, self.state.current_frame)
                self.state.set_current_frame(self.state.current_frame)

                self.detector.terminate()
            except Exception as e:
                self.err_signal.emit(str(e))
