from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QGroupBox, QStyle, qApp, QRadioButton
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

from decisionlabeling.constants.constants import FrameRate
from decisionlabeling.models import KeyboardListener, FrameMode
from decisionlabeling.models.track_info import Detection
from decisionlabeling.models.polygon import Polygon, Bbox, Keypoints
import time


class PlayerThread(QThread):

    def __init__(self, state):
        super().__init__()

        self.state = state

    def run(self):
        while self.state.frame_mode == FrameMode.CONTROLLED and (
                (self.state.speed_player >= 0 and self.state.current_frame < self.state.nb_frames - 1) or
                (self.state.speed_player < 0 < self.state.current_frame)
        ):
            # if not self.state.drawing:
            self.state.increase_current_frame()
            time.sleep(1 / self.state.FRAME_RATE)


class PlayerWidget(QGroupBox, KeyboardListener):
    def __init__(self, state):
        super().__init__("Player")

        self.state = state

        self.thread = PlayerThread(self.state)
        self.thread.finished.connect(self.on_player_finished)

        layout = QHBoxLayout()

        # self.skip_backward_button = QPushButton()
        # self.skip_backward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        # self.skip_backward_button.clicked.connect(self.on_skip_backward_clicked)

        # self.speed_left_button = QPushButton()
        # self.speed_left_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        # self.speed_left_button.clicked.connect(self.on_speed_left_clicked)

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.on_play_clicked)

        # self.slow_play_button = QPushButton()
        # self.slow_play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        # self.slow_play_button.clicked.connect(self.on_default_play)

        self.pause_button = QPushButton()
        self.pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_button.clicked.connect(self.on_pause_clicked)

        self.radiobutton = QRadioButton("Video Tag")
        self.radiobutton.setChecked(False)
        self.radiobutton.toggled.connect(self.on_radio_checked)


        # self.skip_forward_button = QPushButton()
        # self.skip_forward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        # self.skip_forward_button.clicked.connect(self.on_skip_forward_clicked)

        # self.speed_right_button = QPushButton()
        # self.speed_right_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        # self.speed_right_button.clicked.connect(self.on_speed_right_clicked)

        # layout.addWidget(self.speed_left_button)
        # layout.addWidget(self.slow_play_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.radiobutton)
        # layout.addWidget(self.speed_right_button)

        self.setLayout(layout)

        self.pause_button.hide()

    def on_player_finished(self):
        self.pause_button.hide()
        self.play_button.show()

        # self.speed_left_button.setText("")
        # self.speed_right_button.setText("")

    def on_play_clicked(self, frame_rate):
        self.state.FRAME_RATE= frame_rate
        # self.speed_left_button.setText("")
        self.state.speed_player = 1
        # self.speed_right_button.setText("")
        # print("Frame number: ", self.state.current_frame)
        # print("Side : ", self.state.side)
        # print("frame rate: ", self.state.frame_rate)

        if not self.thread.isRunning():
            if self.state.is_view_play and self.state.is_tag_play:
                self.state.current_frame = 0
                self.state.is_view_play = False
            self.state.frame_mode = FrameMode.CONTROLLED
            self.thread.start()

            self.play_button.hide()
            self.pause_button.show()


    def on_pause_clicked(self):
        # self.speed_left_button.setText("")
        # self.speed_right_button.setText("")
        # print("Frame number: ", self.state.current_frame)
        print("Side : ", self.state.side)

        if self.thread.isRunning():
            self.state.frame_mode = FrameMode.MANUAL
            self.state.speed_player = 5
            self.thread.wait()

            self.pause_button.hide()
            self.play_button.show()

    def on_key_play_pause(self):
        if self.thread.isRunning():
            self.on_pause_clicked()
        elif self.state.is_view_play:
            self.on_play_clicked(FrameRate.VIEW_FRAME_RATE)
        else:
            self.on_play_clicked(FrameRate.TAG_FRAME_RATE)

    # def on_speed_left_clicked(self):
    #     speed_options = [-10, -15, -20]
    #
    #     if self.state.speed_player in speed_options:
    #         current_speed_idx = speed_options.index(self.state.speed_player)
    #         self.state.speed_player = speed_options[(current_speed_idx + 5) % len(speed_options)]
    #     else:
    #         self.state.speed_player = speed_options[0]
    #
    #     self.on_play_clicked()

        # self.speed_right_button.setText("")
        # self.speed_left_button.setText("x{}".format(abs(self.state.speed_player/5)))

    # def on_speed_right_clicked(self):
    #     speed_options = [+10, +15, +20]
    #
    #     if self.state.speed_player in speed_options:
    #         current_speed_idx = speed_options.index(self.state.speed_player)
    #         self.state.speed_player = speed_options[(current_speed_idx + 5) % len(speed_options)]
    #     else:
    #         self.state.speed_player = speed_options[0]
    #
    #     self.on_play_clicked()

        # self.speed_left_button.setText("")
        # self.speed_right_button.setText("x{}".format(self.state.speed_player/5))

    def on_slow_clicked(self):
        speed_options = [+10, +15, +20]

        # if self.state.speed_player in speed_options:
        current_speed_idx = 0#speed_options.index(self.state.speed_player)
        self.state.speed_player = speed_options[(current_speed_idx + 1) % len(speed_options)]
        # else:
        #     self.state.speed_player = speed_options[0]
        #
        # self.on_play_clicked()
        #
        # self.speed_left_button.setText("")
        # self.speed_right_button.setText("x{}".format(self.state.speed_player))

    def on_skip_backward_clicked(self):
        self.state.set_current_frame(0)

    def on_skip_forward_clicked(self):
        self.state.set_current_frame(self.state.nb_frames - 1)

    def on_key_x(self):
        # if self.state.side != "left":
        self.state.set_side("left")
        self.update_state()
        # else:
        #     self.state.side = None

    def on_key_v(self):
        # if self.state.side != "right":
        self.state.set_side("right")
        self.update_state()
        # else:
        #     self.state.side = None

    def on_key_t(self):
        self.on_video_tag()

    def on_video_tag(self):
        self.state.is_tag_play = True
        self.on_play_clicked(FrameRate.TAG_FRAME_RATE)
        if self.state.is_view_play and self.state.is_tag_play:
            self.state.current_frame = 0
            self.state.is_view_play = False
        self.update_state()

    def on_radio_checked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.on_video_tag()

    def update_state(self):
        self.state.img_viewer.on_current_frame_change()
        try:
            self.state.track_info.last_tagged_side= list(self.state.track_info.tagged_frames.keys())[-1]
        except IndexError:
            print("First tagged frame: "+ str(self.state.current_frame))
        self.state.track_info.tagged_frames[self.state.current_frame] = self.state.side
        self.state.track_info.total_frames = self.state.nb_frames