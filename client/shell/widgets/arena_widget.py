"""
GameArena 风格壳层：侧边栏 + 主视图 + 右侧好友/聊天

该组件负责视图切换（lobby / room / friends / rank / settings）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from ..styles.theme import CURRENT_THEME as t
from .arena_lobby_view import ArenaLobbyView
from .arena_room_view import ArenaRoomView, RoomDisplay
from .right_panel_widget import RightPanelWidget
from .sidebar_widget import SidebarWidget
from .settings_widget import SettingsWidget


@dataclass(frozen=True)
class GameMeta:
    game_id: str
    title: str
    category: str = "对战"
    icon: str = "🎮"


class CenteredPlaceholder(QFrame):
    def __init__(self, text: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {t.bg_base}; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel(text)
        label.setStyleSheet(f"font-size: 16px; color: {t.text_caption}; font-weight: 800;")
        layout.addWidget(label)


class ArenaWidget(QWidget):
    """主 UI 壳层"""

    logout_requested = Signal()
    game_entered = Signal(str)  # game_id
    room_joined = Signal(str)
    create_room_requested = Signal()
    quick_match_requested = Signal()
    leave_room_requested = Signal()
    start_game_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None, demo_mode: bool = False):
        super().__init__(parent)

        self.sidebar = SidebarWidget()
        self.right_panel = RightPanelWidget()
        self.stack = QStackedWidget()

        # Pages
        self.lobby_view = ArenaLobbyView()
        self.room_view = ArenaRoomView()
        self._page_friends = CenteredPlaceholder("好友管理页面 (Demo)")
        self._page_rank = CenteredPlaceholder("排行榜页面 (Demo)")
        self._page_settings = SettingsWidget()

        self._game_meta: Optional[GameMeta] = None

        self._setup_ui()
        self._wire_signals()

        self.set_active_tab("lobby")
        if demo_mode:
            self.load_demo_data()

    # ========== 对外接口 ==========
    def set_user(self, nickname: str, avatar: str = "👤", level: int = 0):
        self.sidebar.set_user(nickname=nickname, avatar=avatar, level=level)
        self.lobby_view.set_user(nickname)
        self.room_view.set_user(nickname=nickname, avatar=avatar, rank="Diamond II")

    def set_connection_status(self, connected: bool, text: str = ""):
        self.lobby_view.set_connection_status(connected, text)

    def set_active_tab(self, tab_id: str):
        self.sidebar.set_active_tab(tab_id)
        index_map = {
            "lobby": self.stack.indexOf(self.lobby_view),
            "room": self.stack.indexOf(self.room_view),
            "friends": self.stack.indexOf(self._page_friends),
            "rank": self.stack.indexOf(self._page_rank),
            "settings": self.stack.indexOf(self._page_settings),
        }
        target = index_map.get(tab_id)
        if target is not None and target >= 0:
            self.stack.setCurrentIndex(target)

    def enter_room(self, meta: GameMeta):
        self._game_meta = meta

        self.room_view.set_room(RoomDisplay(room_id="8293", title=meta.title, category=meta.category))
        self.room_view.begin_matchmaking()

        self.set_active_tab("room")
        self.game_entered.emit(meta.game_id)

    def load_demo_data(self):
        """填充演示数据（好友/房间/聊天）。"""
        self.right_panel.friends_widget.set_friends(
            [
                {
                    "user_id": "u1",
                    "nickname": "CyberNinja",
                    "avatar": "🥷",
                    "is_online": True,
                    "in_game": True,
                    "current_game": "五子棋",
                },
                {"user_id": "u2", "nickname": "Sakura_Chan", "avatar": "🌸", "is_online": True},
                {"user_id": "u3", "nickname": "NoobMaster69", "avatar": "🧑", "is_online": False},
                {"user_id": "u4", "nickname": "ProGamer_X", "avatar": "🎯", "is_online": True},
            ]
        )

        self.lobby_view.rooms_widget.set_rooms(
            [
                {
                    "room_id": "1001",
                    "name": "新手友好局",
                    "game_type": "gomoku",
                    "current_players": 1,
                    "max_players": 2,
                    "host_name": "小白",
                },
                {
                    "room_id": "1002",
                    "name": "激烈对战",
                    "game_type": "shooter2d",
                    "current_players": 5,
                    "max_players": 8,
                    "host_name": "枪神",
                },
                {
                    "room_id": "1003",
                    "name": "狼人杀欢乐局",
                    "game_type": "werewolf",
                    "current_players": 8,
                    "max_players": 12,
                    "host_name": "预言家",
                },
            ]
        )

        self.right_panel.chat_widget.set_local_user("self")
        self.right_panel.chat_widget.add_message(
            {
                "sender_id": "system",
                "sender_name": "System",
                "sender_color": t.text_caption,
                "content": "欢迎来到 Aether Party 对战大厅！",
                "time": "10:00",
            }
        )

    # ========== 内部 ==========
    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {t.bg_base};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.sidebar)

        center = QFrame()
        center.setStyleSheet(f"background-color: {t.bg_base}; border: none;")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.stack.addWidget(self.lobby_view)
        self.stack.addWidget(self.room_view)
        self.stack.addWidget(self._page_friends)
        self.stack.addWidget(self._page_rank)
        self.stack.addWidget(self._page_settings)

        center_layout.addWidget(self.stack, 1)

        layout.addWidget(center, 1)
        layout.addWidget(self.right_panel)

    def _wire_signals(self):
        self.sidebar.tab_changed.connect(self._on_tab_changed)
        self.right_panel.close_requested.connect(lambda: self.right_panel.set_open(False))
        self._page_settings.logout_requested.connect(self.logout_requested.emit)

        self.lobby_view.game_selected.connect(self._on_game_selected)
        self.lobby_view.room_joined.connect(self.room_joined.emit)
        self.lobby_view.create_room_requested.connect(self.create_room_requested.emit)
        self.lobby_view.quick_match_requested.connect(self._on_quick_match)

        self.room_view.leave_requested.connect(self._on_leave_room)
        self.room_view.start_requested.connect(self._on_room_start)
        self.room_view.invite_requested.connect(self._on_invite)

    def _on_tab_changed(self, tab_id: str):
        # 切回大厅时清空房间选择
        if tab_id == "lobby":
            self._game_meta = None
        self.set_active_tab(tab_id)

    def _on_game_selected(self, game_id: str):
        meta_map = {
            "gomoku": GameMeta(game_id="gomoku", title="五子棋", category="策略", icon="⚫"),
            "shooter2d": GameMeta(game_id="shooter2d", title="2D 射击", category="动作", icon="🔫"),
            "werewolf": GameMeta(game_id="werewolf", title="狼人杀", category="社交", icon="🐺"),
            "monopoly": GameMeta(game_id="monopoly", title="大富翁", category="聚会", icon="🎲"),
            "racing": GameMeta(game_id="racing", title="赛车竞速", category="竞速", icon="🏎️"),
        }
        self.enter_room(meta_map.get(game_id, GameMeta(game_id=game_id, title=game_id)))

    def _on_quick_match(self):
        self.quick_match_requested.emit()
        self._on_game_selected("shooter2d")

    def _on_leave_room(self):
        self.leave_room_requested.emit()
        self.set_active_tab("lobby")

    def _on_room_start(self):
        # 匹配中点击 = 取消；就绪后点击 = 开始（Demo：在聊天里提示）
        if getattr(self.room_view, "_is_matching", False):
            self.room_view.cancel_matchmaking()
            return
        self.start_game_requested.emit()

    def _on_invite(self):
        self.set_active_tab("friends")
