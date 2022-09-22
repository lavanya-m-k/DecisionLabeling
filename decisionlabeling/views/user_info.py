import os
import json
import socket

from PyQt5.QtWidgets import QGroupBox, QLabel, QLineEdit, QFormLayout, QPushButton, QMessageBox
from decisionlabeling.models import StateListener

class UserInfo(QGroupBox, StateListener):
    def __init__(self, state):
        super().__init__("User Info")

        self.state = state
        self.state.add_listener(self)

        # self.ssh_client = paramiko.SSHClient()
        # self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        form_layout = QFormLayout()

        self.username = QLineEdit()
        form_layout.addRow(QLabel("Username:"), self.username)

        # self.password = QLineEdit()
        # self.password.setEchoMode(QLineEdit.Password)
        # form_layout.addRow(QLabel("Password:"), self.password)

        self.connect_button = QPushButton("Submit")
        self.connect_button.clicked.connect(self.on_connect_button_clicked)
        form_layout.addRow(self.connect_button)

        self.setLayout(form_layout)
        self.setFixedWidth(250)

        self.load_credentials()

    def load_credentials(self):
        # self.hostname.setText(self.state.ssh_credentials.hostname)
        self.username.setText(self.state.ssh_credentials.username)
        # self.password.setText(self.state.ssh_credentials.password)

    def on_connect_button_clicked(self):
        username = self.username.text()
        self.state.user_name = username

        # self.save_credentials(hostname, username, password)
        self.connect_button.setText("Updated")
        self.connect_button.setEnabled(False)
        QMessageBox.information(self, "", "Updated!")
