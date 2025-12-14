"""
Room 视图（GameArena 风格）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..styles.theme import CURRENT_THEME as t


@dataclass(frozen=True)
class RoomDisplay:
    room_id: str
    title: str
    category: str = "对战"


class ArenaRoomView(QWidget):
    """房间页：匹配/准备 UI + 游戏容器"""

    leave_requested = Signal()
    start_requested = Signal()
    invite_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._room = RoomDisplay(room_id="8293", title="Game Room", category="对战")
        self._is_matching = False
        self._match_timer: Optional[QTimer] = None

        self._room_badge = QLabel()
        self._title = QLabel()
        self._subtitle = QLabel()
        self._opponent_status = QLabel()
        self._start_btn = QPushButton()
        self._stack: Optional[QStackedWidget] = None
        self._match_page: Optional[QWidget] = None
        self._game_page: Optional[QWidget] = None
        self._game_layout: Optional[QVBoxLayout] = None
        self._game_title = QLabel("游戏中")
        self._game_widget: Optional[QWidget] = None
        self._game_placeholder: Optional[QLabel] = None

        self._setup_ui()
        self.set_room(self._room)
        self.set_matching(False)

    def set_room(self, room: RoomDisplay):
        self._room = room
        self._room_badge.setText(f"🟢 房间号: #{room.room_id}")
        self._title.setText(room.title)
        self._subtitle.setText(f"{room.category}模式 · 休闲匹配")

    def set_user(self, nickname: str, avatar: str = "👤", rank: str = "Diamond II"):
        self._me_name.setText(nickname or "Player")
        self._me_avatar.setText(avatar or "👤")
        self._me_rank.setText(rank)

    def set_opponent(self, nickname: str, avatar: str = "👤", rank: str = "Grandmaster"):
        self._op_name.setText(nickname or "Opponent")
        self._op_avatar.setText(avatar or "👤")
        self._op_rank.setText(rank)

    def begin_matchmaking(self, duration_ms: int = 2500):
        self.set_matching(True)
        if self._match_timer is None:
            self._match_timer = QTimer(self)
            self._match_timer.setSingleShot(True)
            self._match_timer.timeout.connect(lambda: self.set_matching(False))
        self._match_timer.stop()
        self._match_timer.start(duration_ms)

    def cancel_matchmaking(self):
        if self._match_timer:
            self._match_timer.stop()
        self.set_matching(False)

    def set_matching(self, matching: bool):
        self._is_matching = bool(matching)
        if self._is_matching:
            self._opponent_status.setText("寻找对手中...")
            self._opponent_status.setStyleSheet(f"color: {t.text_caption}; font-weight: 700;")
            self._op_container.setStyleSheet(
                f"""
                QFrame {{
                    background-color: rgba(255, 255, 255, 0.55);
                    border: 2px dashed {t.border_normal};
                    border-radius: 90px;
                }}
                """
            )
            self._op_avatar.setText("🔎")
            self._start_btn.setText("取消匹配")
        else:
            self._opponent_status.setText("对手已就位")
            self._opponent_status.setStyleSheet(
                f"""
                color: {t.error};
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
                padding: 6px 12px;
                border-radius: 14px;
                font-weight: 900;
                """
            )
            self._op_container.setStyleSheet(
                f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #DC2626, stop:1 #F97316);
                    border-radius: 90px;
                }}
                """
            )
            # 恢复头像（如果调用方未设置）
            if self._op_avatar.text() == "🔎":
                self._op_avatar.setText("😈")
            self._start_btn.setText("⚔️ 开始游戏")

        self._invite_btn.setEnabled(not self._is_matching)
        self._start_btn.setEnabled(True)

    def show_match_ui(self):
        if self._stack and self._match_page:
            self._stack.setCurrentWidget(self._match_page)

    def show_game(self, title: str, widget: QWidget):
        """展示游戏容器（由 MainWindow 注入具体游戏 Widget）"""
        self._game_title.setText(title or "游戏中")

        if self._game_placeholder:
            self._game_placeholder.hide()

        if self._game_widget:
            self._game_widget.setParent(None)
            self._game_widget.deleteLater()
            self._game_widget = None

        self._game_widget = widget
        if self._game_layout:
            self._game_layout.addWidget(widget, 1)

        if self._stack and self._game_page:
            self._stack.setCurrentWidget(self._game_page)

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {t.bg_base};")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        # Top bar
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(12)

        leave_btn = QPushButton("← 离开房间")
        leave_btn.setCursor(Qt.PointingHandCursor)
        leave_btn.setFixedHeight(40)
        leave_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.88);
                border: 1px solid {t.border_normal};
                border-radius: 18px;
                padding: 0 14px;
                font-weight: 900;
                color: {t.text_display};
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
            """
        )
        leave_btn.clicked.connect(self.leave_requested.emit)
        top.addWidget(leave_btn)
        top.addStretch()
        root.addLayout(top)

        # Stack: match page / game page
        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        # ===== Match page =====
        self._match_page = QWidget()
        layout = QVBoxLayout(self._match_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # Header
        header = QVBoxLayout()
        header.setSpacing(10)
        header.setAlignment(Qt.AlignHCenter)

        self._room_badge.setStyleSheet(
            f"""
            background-color: rgba(255, 255, 255, 0.88);
            border: 1px solid {t.border_normal};
            border-radius: 16px;
            padding: 6px 12px;
            font-weight: 900;
            color: {t.text_caption};
            """
        )
        header.addWidget(self._room_badge, 0, alignment=Qt.AlignHCenter)

        self._title.setStyleSheet(f"font-size: 30px; font-weight: 900; color: {t.text_display};")
        header.addWidget(self._title, 0, alignment=Qt.AlignHCenter)

        self._subtitle.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t.text_caption};")
        header.addWidget(self._subtitle, 0, alignment=Qt.AlignHCenter)

        layout.addLayout(header)
        layout.addSpacing(10)

        # VS area
        vs_row = QHBoxLayout()
        vs_row.setContentsMargins(0, 0, 0, 0)
        vs_row.setSpacing(24)
        vs_row.setAlignment(Qt.AlignHCenter)

        # Me
        self._me_avatar, self._me_name, self._me_rank = self._build_player_card(
            gradient=(t.primary, "#7C3AED"),
            status_text="准备就绪",
            status_bg=(t.primary, "#7C3AED"),
        )
        vs_row.addWidget(self._me_card, 0, alignment=Qt.AlignTop)

        # VS badge
        vs_badge = QLabel("VS")
        vs_badge.setStyleSheet(
            """
            font-size: 64px;
            font-weight: 900;
            color: transparent;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EF4444, stop:1 #F97316);
            -qt-background-role: none;
            """
        )
        # Qt 不支持 background-clip:text；用纯色替代更稳
        vs_badge.setStyleSheet("font-size: 64px; font-weight: 900; color: #EF4444;")
        vs_row.addWidget(vs_badge, 0, alignment=Qt.AlignVCenter)

        # Opponent
        self._op_avatar, self._op_name, self._op_rank = self._build_player_card(
            gradient=("#DC2626", "#F97316"),
            status_text="寻找对手中...",
            status_bg=None,
            dashed=True,
        )
        vs_row.addWidget(self._op_card, 0, alignment=Qt.AlignTop)

        layout.addLayout(vs_row, 1)

        # Status line under opponent
        status_row = QHBoxLayout()
        status_row.addStretch()
        status_row.addWidget(self._opponent_status)
        status_row.addStretch()
        layout.addLayout(status_row)

        # Bottom actions
        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(14)
        actions.setAlignment(Qt.AlignHCenter)

        self._invite_btn = QPushButton("邀请好友")
        self._invite_btn.setCursor(Qt.PointingHandCursor)
        self._invite_btn.setFixedSize(140, 44)
        self._invite_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.88);
                border: 1px solid {t.border_normal};
                border-radius: 18px;
                font-weight: 900;
                color: {t.text_display};
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
            QPushButton:disabled {{
                color: {t.text_placeholder};
            }}
            """
        )
        self._invite_btn.clicked.connect(self.invite_requested.emit)
        actions.addWidget(self._invite_btn)

        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.setFixedSize(180, 44)
        self._start_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t.primary}, stop:1 #7C3AED);
                border: none;
                border-radius: 18px;
                font-weight: 900;
                color: white;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t.primary_hover}, stop:1 #8B5CF6);
            }}
            """
        )
        self._start_btn.clicked.connect(self.start_requested.emit)
        actions.addWidget(self._start_btn)

        layout.addLayout(actions)

        self._stack.addWidget(self._match_page)

        # ===== Game page =====
        self._game_page = QWidget()
        self._game_layout = QVBoxLayout(self._game_page)
        self._game_layout.setContentsMargins(0, 0, 0, 0)
        self._game_layout.setSpacing(12)

        self._game_title.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {t.text_display};")
        self._game_layout.addWidget(self._game_title, 0)

        self._game_placeholder = QLabel("等待游戏启动...")
        self._game_placeholder.setAlignment(Qt.AlignCenter)
        self._game_placeholder.setStyleSheet(
            f"color: {t.text_caption}; font-size: 13px; font-weight: 700;"
        )
        self._game_layout.addWidget(self._game_placeholder, 1)

        self._stack.addWidget(self._game_page)
        self._stack.setCurrentWidget(self._match_page)

    def _build_player_card(
        self,
        gradient: tuple[str, str],
        status_text: str,
        status_bg: Optional[tuple[str, str]],
        dashed: bool = False,
    ):
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(10)
        outer_layout.setAlignment(Qt.AlignHCenter)

        # Avatar ring
        ring = QFrame()
        ring.setFixedSize(140, 140)
        ring_style = (
            f"border: 2px dashed {t.border_normal};"
            if dashed
            else "border: none;"
        )
        ring.setStyleSheet(
            f"""
            QFrame {{
                {ring_style}
                border-radius: 70px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {gradient[0]}, stop:1 {gradient[1]});
            }}
            """
        )
        ring_layout = QVBoxLayout(ring)
        ring_layout.setContentsMargins(10, 10, 10, 10)

        avatar = QLabel("👤")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("font-size: 42px; color: white; background: transparent;")
        ring_layout.addWidget(avatar, 1)

        # Status pill
        status = QLabel(status_text)
        if status_bg:
            status.setStyleSheet(
                f"""
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {status_bg[0]}, stop:1 {status_bg[1]});
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 900;
                """
            )
        else:
            status.setStyleSheet(f"color: {t.text_caption}; font-size: 11px; font-weight: 800;")

        outer_layout.addWidget(ring, 0, alignment=Qt.AlignHCenter)
        outer_layout.addWidget(status, 0, alignment=Qt.AlignHCenter)

        name = QLabel("Player")
        name.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {t.text_display};")
        outer_layout.addWidget(name, 0, alignment=Qt.AlignHCenter)

        rank = QLabel("Diamond II")
        rank.setStyleSheet(
            f"""
            background-color: rgba(255, 255, 255, 0.88);
            border: 1px solid {t.border_light};
            border-radius: 14px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 900;
            color: {t.text_display};
            """
        )
        outer_layout.addWidget(rank, 0, alignment=Qt.AlignHCenter)

        # store
        if dashed:
            self._op_card = outer
            self._op_container = ring
        else:
            self._me_card = outer

        return avatar, name, rank
