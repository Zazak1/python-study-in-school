"""
注册对话框（MVP）
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ..styles.theme import CURRENT_THEME as t


class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("注册账号")
        self.setFixedSize(420, 420)
        self.setStyleSheet(f"background-color: {t.bg_card};")

        self._username = QLineEdit()
        self._username.setPlaceholderText("用户名")
        self._username.setFixedHeight(44)

        self._nickname = QLineEdit()
        self._nickname.setPlaceholderText("昵称（可选，默认同用户名）")
        self._nickname.setFixedHeight(44)

        self._password = QLineEdit()
        self._password.setPlaceholderText("密码")
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setFixedHeight(44)

        self._confirm = QLineEdit()
        self._confirm.setPlaceholderText("确认密码")
        self._confirm.setEchoMode(QLineEdit.Password)
        self._confirm.setFixedHeight(44)
        self._confirm.returnPressed.connect(self._on_submit)

        self._error = QLabel("")
        self._error.setWordWrap(True)
        self._error.setStyleSheet(f"color: {t.error}; font-size: 12px; font-weight: 700;")

        title = QLabel("创建新账号")
        title.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {t.text_display};")

        hint = QLabel("注册成功后请返回登录。")
        hint.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t.text_caption};")

        cancel = QPushButton("取消")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.setFixedHeight(44)
        cancel.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {t.bg_base};
                color: {t.text_body};
                border: 1px solid {t.border_normal};
                border-radius: 10px;
                font-size: 14px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
            """
        )
        cancel.clicked.connect(self.reject)

        submit = QPushButton("注册")
        submit.setCursor(Qt.PointingHandCursor)
        submit.setFixedHeight(44)
        submit.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {t.primary};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 900;
            }}
            QPushButton:hover {{
                background-color: {t.primary_hover};
            }}
            """
        )
        submit.clicked.connect(self._on_submit)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addWidget(cancel)
        actions.addWidget(submit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(14)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(6)
        layout.addWidget(self._username)
        layout.addWidget(self._nickname)
        layout.addWidget(self._password)
        layout.addWidget(self._confirm)
        layout.addWidget(self._error)
        layout.addStretch()
        layout.addLayout(actions)

    def get_register_data(self) -> dict:
        username = self._username.text().strip()
        nickname = self._nickname.text().strip() or username
        password = self._password.text()
        return {"username": username, "nickname": nickname, "password": password}

    def _on_submit(self):
        username = self._username.text().strip()
        password = self._password.text()
        confirm = self._confirm.text()

        if not username:
            self._error.setText("请输入用户名。")
            return
        if not password:
            self._error.setText("请输入密码。")
            return
        if password != confirm:
            self._error.setText("两次输入的密码不一致。")
            return

        self._error.setText("")
        self.accept()

