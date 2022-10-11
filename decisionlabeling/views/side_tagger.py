import cv2
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton
from decisionlabeling.models import StateListener
from PyQt5.QtCore import QThread
from decisionlabeling.styles import Theme


class SideTagger(QGroupBox, StateListener):
    def __init__(self, state):
        super().__init__("Side")

        self.state = state
        self.thickness = 2
        self.font = cv2.QT_FONT_NORMAL
        self.fontScale = 3
        state.add_listener(self)

        self.side_tag_thread = SideTagThread(self.state)

        self.left_theme_button = QPushButton("Left")
        self.left_theme_button.clicked.connect(self.on_left_clicked)

        self.right_theme_button = QPushButton("Right")
        self.right_theme_button.clicked.connect(self.on_right_clicked)

        layout = QHBoxLayout()
        layout.addWidget(self.left_theme_button)
        layout.addWidget(self.right_theme_button)
        self.setLayout(layout)

    def update_state(self):
        self.state.img_viewer.on_current_frame_change()
        try:
            self.state.track_info.last_tagged_side = list(self.state.track_info.tagged_frames.keys())[-1]
        except IndexError:
            print("First tagged frame: " + str(self.state.current_frame))
        self.state.track_info.tagged_frames[self.state.current_frame] = self.state.side
        self.state.track_info.total_frames = self.state.nb_frames

    def on_left_clicked(self):
        # if self.state.side != "left":
        self.state.set_side("left")
        self.update_state()
        # else:
        #     self.state.side = None


    def on_right_clicked(self):
        # self.state.set_theme(Theme.LIGHT)
        # self.state.img_viewer.img= cv2.putText(self.state.img_viewer.img, "Right", (600, 600),
        #             self.font, self.fontScale, (50,205,50), self.thickness, cv2.LINE_AA, False)
        # if self.state.side != "right":
        self.state.set_side("right")
        self.update_state()
        # else:
        #     self.state.side = None

class SideTagThread(QThread):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.thickness = 2
        self.font = cv2.QT_FONT_NORMAL
        self.fontScale = 7

    def run(self):
        self.state.tracking_server_running = True
        self.state.detection_server_running = True
        # self.state.img_viewer.img = cv2.putText(self.state.img_viewer.img, "Left", (100, 600),
        #                                         self.font, self.fontScale, (178, 34, 34), self.thickness, cv2.LINE_AA,
        #                                         False)
        # self.state.set_side("left")
        self.state.img_viewer.on_current_frame_change()
