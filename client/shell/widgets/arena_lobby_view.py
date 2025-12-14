"""
Lobby 视图（GameArena 风格）
"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..styles.theme import CURRENT_THEME as t
from .game_card import GameCard
from .rooms_widget import RoomsWidget


class ArenaLobbyView(QWidget):
    """大厅页：Header + Hero + 游戏卡片网格 + 房间列表"""

    game_selected = Signal(str)
    quick_match_requested = Signal()
    create_room_requested = Signal()
    room_joined = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._user_name = "Player"

        self._title = QLabel()
        self._subtitle = QLabel("今天想玩点什么？")
        self._conn = QLabel("")
        self._search = QLineEdit()

        self.rooms_widget = RoomsWidget()
        self.rooms_widget.join_room.connect(self.room_joined.emit)
        self.rooms_widget.create_room.connect(self.create_room_requested.emit)
        self.rooms_widget.quick_match.connect(self.quick_match_requested.emit)

        self._setup_ui()
        self.set_user(self._user_name)

    def set_user(self, nickname: str):
        self._user_name = nickname or "Player"
        self._title.setText(f"你好, {self._user_name}  👋")

    def set_connection_status(self, connected: bool, text: str = ""):
        if connected:
            self._conn.setText(f"🟢 {text or '已连接服务器'}")
            self._conn.setStyleSheet(f"color: {t.success}; font-size: 12px; font-weight: 700;")
        else:
            self._conn.setText(f"🔴 {text or '连接断开'}")
            self._conn.setStyleSheet(f"color: {t.error}; font-size: 12px; font-weight: 700;")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        layout.addWidget(scroll, 1)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(22)
        scroll.setWidget(content)

        # ===== Header =====
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(14)

        left = QVBoxLayout()
        left.setSpacing(4)
        self._title.setStyleSheet(
            f"font-size: 28px; font-weight: 900; color: {t.text_display}; letter-spacing: -0.5px;"
        )
        self._subtitle.setStyleSheet(f"font-size: 13px; color: {t.text_caption}; font-weight: 600;")
        left.addWidget(self._title)
        left.addWidget(self._subtitle)
        left.addWidget(self._conn)
        header.addLayout(left, 1)

        # Search
        search_wrap = QFrame()
        search_wrap.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_normal};
                border-radius: 18px;
            }}
            """
        )
        search_layout = QHBoxLayout(search_wrap)
        search_layout.setContentsMargins(12, 8, 12, 8)
        search_layout.setSpacing(10)
        icon = QLabel("🔎")
        icon.setStyleSheet(f"color: {t.text_placeholder}; font-size: 14px;")
        search_layout.addWidget(icon)
        self._search.setPlaceholderText("搜索游戏...")
        self._search.setFixedWidth(260)
        self._search.setStyleSheet(
            f"""
            QLineEdit {{
                border: none;
                background: transparent;
                padding: 0;
                color: {t.text_display};
                font-weight: 600;
            }}
            """
        )
        search_layout.addWidget(self._search)
        header.addWidget(search_wrap)

        # Bell
        bell = QPushButton("🔔")
        bell.setCursor(Qt.PointingHandCursor)
        bell.setFixedSize(40, 40)
        bell.setToolTip("通知")
        bell.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_normal};
                border-radius: 18px;
                font-size: 16px;
                color: {t.text_caption};
            }}
            QPushButton:hover {{
                background-color: {t.primary_bg};
                border-color: {t.primary};
                color: {t.primary};
            }}
            """
        )
        header.addWidget(bell)

        content_layout.addLayout(header)

        # ===== Hero =====
        hero = QFrame()
        hero.setFixedHeight(220)
        hero.setStyleSheet(
            f"""
            QFrame {{
                border-radius: 28px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t.primary}, stop:1 #7C3AED);
            }}
            """
        )
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(26, 22, 26, 22)
        hero_layout.setSpacing(12)

        tags = QHBoxLayout()
        tags.setSpacing(10)

        tag1 = QLabel("🔥 今日推荐")
        tag1.setStyleSheet(
            """
            color: white;
            background-color: rgba(255, 255, 255, 0.20);
            border: 1px solid rgba(255, 255, 255, 0.25);
            padding: 4px 10px;
            border-radius: 14px;
            font-size: 11px;
            font-weight: 900;
            """
        )
        tags.addWidget(tag1)

        tag2 = QLabel("⚡ 双倍积分")
        tag2.setStyleSheet(
            """
            color: rgba(255, 255, 255, 0.92);
            background-color: rgba(0, 0, 0, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 4px 10px;
            border-radius: 14px;
            font-size: 11px;
            font-weight: 800;
            """
        )
        tags.addWidget(tag2)
        tags.addStretch()
        hero_layout.addLayout(tags)

        h_title = QLabel("赛季排位赛 S12")
        h_title.setStyleSheet("color: white; font-size: 34px; font-weight: 900; letter-spacing: -0.5px;")
        hero_layout.addWidget(h_title)

        h_desc = QLabel("全新的排名系统已经上线。立即加入战斗，赢取限定皮肤和海量金币奖励！")
        h_desc.setWordWrap(True)
        h_desc.setStyleSheet("color: rgba(255,255,255,0.92); font-size: 13px; font-weight: 600;")
        hero_layout.addWidget(h_desc)

        hero_layout.addStretch(1)

        cta = QPushButton("▶ 立即匹配")
        cta.setCursor(Qt.PointingHandCursor)
        cta.setFixedHeight(44)
        cta.setStyleSheet(
            f"""
            QPushButton {{
                background-color: white;
                color: {t.primary};
                border: none;
                border-radius: 18px;
                padding: 0 18px;
                font-size: 14px;
                font-weight: 900;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
            """
        )
        cta.clicked.connect(lambda: self.game_selected.emit("gomoku"))
        hero_layout.addWidget(cta, 0, alignment=Qt.AlignLeft)

        content_layout.addWidget(hero)

        # ===== Games =====
        section_title = QHBoxLayout()
        section_title.setSpacing(12)

        st = QLabel("⚔️ 热门对战")
        st.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {t.text_display};")
        section_title.addWidget(st)
        section_title.addStretch()

        view_all = QLabel("查看全部 →")
        view_all.setStyleSheet(f"font-size: 12px; color: {t.text_caption}; font-weight: 800;")
        section_title.addWidget(view_all)

        content_layout.addLayout(section_title)

        grid_wrap = QWidget()
        grid = QGridLayout(grid_wrap)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        game_ids = ["gomoku", "shooter2d", "werewolf", "monopoly", "racing"]
        cols = 3
        for idx, gid in enumerate(game_ids):
            card = GameCard(gid)
            card.clicked.connect(self.game_selected.emit)
            grid.addWidget(card, idx // cols, idx % cols)

        # 占位让布局不贴边
        grid.setColumnStretch(cols, 1)
        content_layout.addWidget(grid_wrap)

        # ===== Rooms =====
        rooms_card = QFrame()
        rooms_card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 22px;
            }}
            """
        )
        rooms_layout = QVBoxLayout(rooms_card)
        rooms_layout.setContentsMargins(18, 18, 18, 18)
        rooms_layout.addWidget(self.rooms_widget)
        content_layout.addWidget(rooms_card)

