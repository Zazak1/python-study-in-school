"""
侧边栏导航（GameArena 风格）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..styles.theme import CURRENT_THEME as t


@dataclass(frozen=True)
class NavItem:
    id: str
    icon: str
    label: str


class SidebarWidget(QFrame):
    """左侧导航栏（固定宽度）"""

    tab_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self._active_tab = "lobby"
        self._buttons: Dict[str, QPushButton] = {}

        self._avatar = QLabel("👤")
        self._name = QLabel("游客用户")
        self._level = QLabel("Lv.0")

        self._setup_ui()
        self.set_active_tab(self._active_tab)

    def set_user(self, nickname: str, avatar: str = "👤", level: int = 0):
        self._avatar.setText(avatar or "👤")
        self._name.setText(nickname or "游客用户")
        self._level.setText(f"Lv.{level}")

    def set_active_tab(self, tab_id: str):
        self._active_tab = tab_id
        for tid, btn in self._buttons.items():
            self._apply_nav_style(btn, active=(tid == tab_id))

    def _setup_ui(self):
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.88);
                border-right: 1px solid {t.border_normal};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(14)

        # Logo
        header = QHBoxLayout()
        header.setSpacing(10)

        logo_box = QFrame()
        logo_box.setFixedSize(40, 40)
        logo_box.setStyleSheet(
            f"""
            QFrame {{
                background: {t.primary};
                border-radius: 12px;
            }}
            """
        )
        logo_icon = QLabel("🎮", logo_box)
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_icon.setStyleSheet("color: white; font-size: 18px; background: transparent;")
        logo_icon.setGeometry(0, 0, 40, 40)

        title = QLabel("ARENA")
        title.setStyleSheet(
            f"""
            font-size: 18px;
            font-weight: 900;
            color: {t.primary};
            letter-spacing: -0.5px;
            """
        )

        header.addWidget(logo_box)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Nav
        nav_items = [
            NavItem(id="lobby", icon="🎮", label="游戏大厅"),
            NavItem(id="friends", icon="👥", label="我的好友"),
            NavItem(id="rank", icon="🏆", label="排行榜"),
            NavItem(id="settings", icon="⚙️", label="设置"),
        ]

        nav = QVBoxLayout()
        nav.setSpacing(8)
        for item in nav_items:
            btn = QPushButton(f"{item.icon}  {item.label}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda _=False, tid=item.id: self.tab_changed.emit(tid))
            self._buttons[item.id] = btn
            nav.addWidget(btn)
        nav.addStretch()
        layout.addLayout(nav, 1)

        # User card
        card = QFrame()
        card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_hover};
                border: 1px solid {t.border_light};
                border-radius: 18px;
            }}
            """
        )
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(10)

        self._avatar.setFixedSize(40, 40)
        self._avatar.setAlignment(Qt.AlignCenter)
        self._avatar.setStyleSheet(
            f"""
            background-color: {t.bg_card};
            border: 1px solid {t.border_light};
            border-radius: 20px;
            font-size: 18px;
            """
        )

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._name.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {t.text_display};")
        self._level.setStyleSheet(f"font-size: 11px; color: {t.text_caption}; font-weight: 600;")
        text_col.addWidget(self._name)
        text_col.addWidget(self._level)

        card_layout.addWidget(self._avatar)
        card_layout.addLayout(text_col, 1)

        layout.addWidget(card)

    def _apply_nav_style(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {t.primary};
                    color: {t.text_white};
                    border: 1px solid {t.primary};
                    border-radius: 14px;
                    font-weight: 800;
                    text-align: left;
                    padding: 0 14px;
                }}
                """
            )
        else:
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    color: {t.text_caption};
                    border: 1px solid transparent;
                    border-radius: 14px;
                    font-weight: 700;
                    text-align: left;
                    padding: 0 14px;
                }}
                QPushButton:hover {{
                    background-color: {t.bg_hover};
                    color: {t.text_display};
                    border-color: {t.border_light};
                }}
                """
            )

