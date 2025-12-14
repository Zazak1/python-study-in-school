"""
右侧面板（好友 + 聊天）- GameArena 风格
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..styles.theme import CURRENT_THEME as t
from .friends_widget import FriendsWidget
from .chat_widget import ChatWidget


class RightPanelWidget(QFrame):
    """右侧抽屉面板（桌面端常驻；可手动关闭/打开）"""

    close_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedWidth(360)
        self._is_open = True

        self.friends_widget = FriendsWidget()
        self.chat_widget = ChatWidget()

        self._setup_ui()

    def set_open(self, open_: bool):
        self._is_open = bool(open_)
        self.setVisible(self._is_open)

    def _setup_ui(self):
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_card};
                border-left: 1px solid {t.border_normal};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.88);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(10)

        title = QLabel("👥 好友与聊天")
        title.setStyleSheet(f"font-size: 14px; font-weight: 900; color: {t.text_display};")
        header_layout.addWidget(title)

        header_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setToolTip("隐藏面板")
        close_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {t.text_caption};
                font-size: 18px;
                font-weight: 900;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
                color: {t.text_display};
            }}
            """
        )
        close_btn.clicked.connect(self.close_requested.emit)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(14)

        friends_card = QFrame()
        friends_card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_base};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
            """
        )
        friends_layout = QVBoxLayout(friends_card)
        friends_layout.setContentsMargins(12, 12, 12, 12)
        friends_layout.addWidget(self.friends_widget)

        chat_card = QFrame()
        chat_card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_base};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
            """
        )
        chat_layout = QVBoxLayout(chat_card)
        chat_layout.setContentsMargins(12, 12, 12, 12)
        chat_layout.addWidget(self.chat_widget)

        content_layout.addWidget(friends_card, 1)
        content_layout.addWidget(chat_card, 1)
        layout.addWidget(content, 1)

