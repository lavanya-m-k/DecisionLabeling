from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
import os
from PyQt5 import QtCore
# ,QtGui
from decisionlabeling.views import *
from decisionlabeling.models import State, StateListener, KeyboardNotifier, FrameMode
from decisionlabeling.styles import Theme
from decisionlabeling.config import DOCS_PATH

class RegisterUser(QDialog):
    def __init__(self):
        super().__init__()
        self.user_name = QLineEdit(self)
        self.button_login = QPushButton('start', self)
        self.button_login.clicked.connect(self.register_user)
        layout = QVBoxLayout(self)
        layout.addWidget(self.user_name)
        layout.addWidget(self.button_login)

    def register_user(self):
        if self.user_name.text() != '':
            user = self.user_name.text()
            print(user)
            self.accept()
        else:
            QMessageBox.warning(
                self, 'Error', 'Bad username')


class MainWindow(QMainWindow):
    def __init__(self, user_name):
        super().__init__()

        self.setWindowTitle("Labeler")

        self.central_widget = CentralWidget(user_name)
        self.central_widget.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.central_widget)
        self.central_widget.setFocus(True)

        self.statusBar()

        mainMenu = self.menuBar()

        fileMenu = mainMenu.addMenu('&File')
        helpMenu = mainMenu.addMenu('&Help')

        close = QAction('Close window', self)
        close.setShortcut('Ctrl+W')
        close.triggered.connect(self.close)
        fileMenu.addAction(close)

        import_action = QAction('Import', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.central_widget.io.on_import_click)
        fileMenu.addAction(import_action)

        export = QAction('Export', self)
        export.setShortcut('Ctrl+E')
        export.triggered.connect(self.central_widget.io.on_export_click)
        fileMenu.addAction(export)

        """save = QAction('Save', self)
        save.setShortcut('Ctrl+S')
        save.triggered.connect()
        fileMenu.addAction(save)"""

        help = QAction('Documentation', self)
        # help.triggered.connect(self.open_url)
        helpMenu.addAction(help)

        self.setCentralWidget(self.central_widget)

        self.show()
        self.center()

    # def open_url(self):
    #     url = QtCore.QUrl('https://github.com/alexandre01/UltimateLabeling')
    #     if not QtGui.QDesktopServices.openUrl(url):
    #         QtGui.QMessageBox.warning(self, 'Open Url', 'Could not open url')

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):
        print("exiting")
        # self.central_widget.ssh_login.closeServers()
        self.central_widget.state.track_info.save_to_disk()
        self.central_widget.state.save_state()


class CentralWidget(QWidget, StateListener):
    def __init__(self, user_name):
        super().__init__()

        self.state = State(user_name)
        # if self.state.user_name==None:
        #     QMessageBox.warning(self, "", "Please enter username")
        # #     control_box = QGroupBox("Control")
        # #     self.user_info = UserInfo(self.state)
        # #     control_layout = QVBoxLayout()
        # #     control_layout.addWidget(self.user_info)
        # #     self.setLayout(control_layout)

        self.state.load_state()
        self.state.add_listener(self)
        # self.state.user_name = user_name

        self.keyboard_notifier = KeyboardNotifier()

        self.video_list_widget = VideoListWidget(self.state)
        self.img_widget = ImageWidget(self.state)
        self.slider = VideoSlider(self.state, self.keyboard_notifier)
        self.player = PlayerWidget(self.state)
        self.side_tagger = SideTagger(self.state)
        self.theme_picker = ThemePicker(self.state)
        self.options = Options(self.state)


        # self.state.FRAME_RATE= 70
        # self.state.frame_mode = FrameMode.MANUAL
        self.thread = PlayerThread(self.state)
        self.thread.start()
        # self.user_info = UserInfo(self.state)

        # self.detection_manager = DetectionManager(self.state, self.ssh_login)
        # self.tracking_manager = TrackingManager(self.state)
        # self.hungarian_button = HungarianManager(self.state)
        # self.info_detection = InfoDetection(self.state)

        self.io = IO(self, self.state)

        self.keyPressEvent = self.keyboard_notifier.keyPressEvent
        self.keyReleaseEvent = self.keyboard_notifier.keyReleaseEvent
        self.keyboard_notifier.add_listeners(self.player, self.slider, self.img_widget)

        # Avoid keyboard not being triggered when focus on some widgets
        self.video_list_widget.setFocusPolicy(Qt.NoFocus)
        self.slider.setFocusPolicy(Qt.NoFocus)
        self.setFocusPolicy(Qt.StrongFocus)

        # Image widget thread signal, update function should always be called from main thread
        self.img_widget.signal.connect(self.img_widget.update)
        self.state.img_viewer = self.img_widget

        self.make_layout()
        self.on_theme_change()

    def make_layout(self):
        main_layout = QHBoxLayout()

        navbar_box = QGroupBox("Videos")
        navbar_layout = QVBoxLayout()
        navbar_layout.addWidget(self.video_list_widget)
        navbar_box.setLayout(navbar_layout)
        main_layout.addWidget(navbar_box)

        image_box = QGroupBox("Image")
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.img_widget)
        image_layout.addWidget(self.slider)
        image_box.setLayout(image_layout)
        main_layout.addWidget(image_box)

        control_box = QGroupBox("Control")
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.player)
        # control_layout.addWidget(self.user_info)
        control_layout.addWidget(self.side_tagger)
        pic = QLabel(control_box)
        pic.setGeometry(10, 10, 400, 100)
        # use full ABSOLUTE path to the image, not relative
        pic.setPixmap(QPixmap(DOCS_PATH + "/keyboard-shortcuts.png"))
        control_layout.addWidget(pic)
        # control_layout.addWidget(self.options)
        # control_layout.addWidget(self.hungarian_button)
        # control_layout.addWidget(self.tracking_manager)
        # control_layout.addWidget(self.info_detection)

        control_layout.addStretch()
        control_box.setLayout(control_layout)
        main_layout.addWidget(control_box)

        self.setLayout(main_layout)

    def on_theme_change(self):
        app.setStyle("Fusion")
        app.setPalette(Theme.get_palette(self.state.theme))


if __name__ == '__main__':
    app = QApplication([])
    # first_window = FirstWindow()
    reg_user = RegisterUser()

    if reg_user.exec_() == 1:
        main_window = MainWindow(reg_user.user_name.text())
        #main_window.show()
        #sys.exit(app.exec_())
    app.exec()


