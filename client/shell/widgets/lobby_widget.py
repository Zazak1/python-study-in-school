"""
大厅主界面组件 - 修复布局
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor

from .game_card import GameCard
from .friends_widget import FriendsWidget
from .rooms_widget import RoomsWidget
from .chat_widget import ChatWidget
from .game_view import GameViewWidget
from ..styles.theme import CURRENT_THEME as t


class UserProfileBar(QWidget):
    """用户信息栏"""
    
    settings_clicked = Signal()
    logout_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 20, 32, 20)
        layout.setSpacing(20)
        
        # 头像 - 固定尺寸
        avatar_container = QWidget()
        avatar_container.setFixedSize(48, 48)
        
        self.avatar_label = QLabel("👤", avatar_container)
        self.avatar_label.setGeometry(0, 0, 48, 48)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet(f"""
            background-color: {t.bg_base};
            border-radius: 24px;
            font-size: 24px;
            border: 2px solid white;
        """)
        
        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.avatar_label.setGraphicsEffect(shadow)
        
        layout.addWidget(avatar_container)
        
        # 用户信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignVCenter)
        
        self.name_label = QLabel("游客用户")
        self.name_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {t.text_display};
        """)
        info_layout.addWidget(self.name_label)
        
        # 状态
        status_layout = QHBoxLayout()
        status_layout.setSpacing(4)
        
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {t.success}; font-size: 10px;")
        status_layout.addWidget(status_dot)
        
        self.status_label = QLabel("在线")
        self.status_label.setStyleSheet(f"font-size: 12px; color: {t.text_caption};")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        info_layout.addLayout(status_layout)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # 货币显示
        coins_widget = QWidget()
        coins_widget.setFixedHeight(36)
        coins_widget.setCursor(Qt.PointingHandCursor)
        coins_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {t.primary_bg};
                border-radius: 18px;
                padding: 0 16px;
            }}
            QWidget:hover {{
                background-color: #DBEAFE;
            }}
        """)
        
        coins_layout = QHBoxLayout(coins_widget)
        coins_layout.setContentsMargins(16, 0, 16, 0)
        coins_layout.setSpacing(8)
        
        coin_icon = QLabel("💎")
        coin_icon.setStyleSheet("font-size: 16px;")
        coins_layout.addWidget(coin_icon)
        
        self.coins_label = QLabel("0")
        self.coins_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 700;
            color: {t.primary};
        """)
        coins_layout.addWidget(self.coins_label)
        
        layout.addWidget(coins_widget)
        
        # 设置按钮
        settings_btn = self._create_icon_btn("⚙️", "设置")
        settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(settings_btn)
        
        # 退出按钮
        logout_btn = self._create_icon_btn("🚪", "退出")
        logout_btn.clicked.connect(self.logout_clicked.emit)
        layout.addWidget(logout_btn)
    
    def _create_icon_btn(self, icon: str, tooltip: str) -> QPushButton:
        btn = QPushButton(icon)
        btn.setFixedSize(40, 40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                border: 1px solid {t.border_light};
                border-radius: 20px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                border-color: {t.primary};
                background-color: {t.bg_hover};
            }}
        """)
        return btn
    
    def set_user(self, user_data: dict):
        self.name_label.setText(user_data.get('nickname', '游客'))
        self.coins_label.setText(str(user_data.get('coins', 0)))
        if user_data.get('avatar'):
            self.avatar_label.setText(user_data['avatar'])


class LobbyWidget(QWidget):
    """大厅主界面"""
    
    game_selected = Signal(str)
    room_joined = Signal(str)
    room_created = Signal()
    quick_match_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_demo_data()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部栏
        self.profile_bar = UserProfileBar()
        self.profile_bar.setStyleSheet(f"""
            background-color: {t.bg_card};
            border-bottom: 1px solid {t.border_light};
        """)
        self.profile_bar.logout_clicked.connect(self.logout_requested.emit)
        main_layout.addWidget(self.profile_bar)
        
        # 内容区
        content = QWidget()
        content.setStyleSheet(f"background-color: {t.bg_base};")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(32, 24, 32, 24)
        content_layout.setSpacing(24)
        
        # 左侧：游戏选择 + 房间列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        
        # 游戏选择标题
        games_title = QLabel("开始游戏")
        games_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {t.text_display};
        """)
        left_layout.addWidget(games_title)
        
        # 游戏卡片 - 水平滚动区域
        games_scroll = QScrollArea()
        games_scroll.setWidgetResizable(True)
        games_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        games_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        games_scroll.setFixedHeight(240)
        games_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        games_container = QWidget()
        games_grid = QHBoxLayout(games_container)
        games_grid.setContentsMargins(0, 0, 0, 0)
        games_grid.setSpacing(16)
        
        game_ids = ['gomoku', 'shooter2d', 'werewolf', 'monopoly', 'racing']
        for game_id in game_ids:
            card = GameCard(game_id)
            card.clicked.connect(self.game_selected.emit)
            games_grid.addWidget(card)
        
        games_grid.addStretch()
        games_scroll.setWidget(games_container)
        left_layout.addWidget(games_scroll)
        
        # 房间列表（卡片容器）
        rooms_card = QFrame()
        rooms_card.setStyleSheet(f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
        """)
        rooms_inner = QVBoxLayout(rooms_card)
        rooms_inner.setContentsMargins(20, 20, 20, 20)
        
        self.rooms_widget = RoomsWidget()
        self.rooms_widget.join_room.connect(self.room_joined.emit)
        self.rooms_widget.create_room.connect(self.room_created.emit)
        self.rooms_widget.quick_match.connect(self.quick_match_requested.emit)
        rooms_inner.addWidget(self.rooms_widget)
        
        left_layout.addWidget(rooms_card, 1)
        
        # 中间：游戏画面（可嵌入渲染，当前显示 render 数据）
        game_panel = QFrame()
        game_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
        """)
        game_layout = QVBoxLayout(game_panel)
        game_layout.setContentsMargins(16, 16, 16, 16)
        game_layout.setSpacing(12)
        
        game_title = QLabel("游戏画面")
        game_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {t.text_display};")
        game_layout.addWidget(game_title)
        
        self.game_view = GameViewWidget()
        game_layout.addWidget(self.game_view, 1)
        
        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(game_panel, 1)
        
        # 右侧：好友 + 聊天
        right_panel = QWidget()
        right_panel.setFixedWidth(340)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(20)
        
        # 好友卡片
        friends_card = QFrame()
        friends_card.setStyleSheet(f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
        """)
        friends_inner = QVBoxLayout(friends_card)
        friends_inner.setContentsMargins(16, 16, 16, 16)
        
        self.friends_widget = FriendsWidget()
        friends_inner.addWidget(self.friends_widget)
        
        right_layout.addWidget(friends_card, 1)
        
        # 聊天卡片
        chat_card = QFrame()
        chat_card.setStyleSheet(f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
        """)
        chat_inner = QVBoxLayout(chat_card)
        chat_inner.setContentsMargins(16, 16, 16, 16)
        
        self.chat_widget = ChatWidget()
        chat_inner.addWidget(self.chat_widget)
        
        right_layout.addWidget(chat_card, 1)
        
        content_layout.addWidget(right_panel)
        
        main_layout.addWidget(content, 1)
        
        # 底部状态栏
        self._setup_status_bar(main_layout)
    
    def _setup_status_bar(self, layout):
        status_bar = QFrame()
        status_bar.setFixedHeight(32)
        status_bar.setStyleSheet(f"""
            background-color: {t.bg_card};
            border-top: 1px solid {t.border_light};
        """)
        
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(32, 0, 32, 0)
        
        self.connection_status = QLabel("🟢 已连接服务器")
        self.connection_status.setStyleSheet(f"""
            font-size: 11px;
            color: {t.success};
        """)
        status_layout.addWidget(self.connection_status)
        
        status_layout.addStretch()
        
        version = QLabel("Aether Party v0.1.0")
        version.setStyleSheet(f"""
            font-size: 11px;
            color: {t.text_caption};
        """)
        status_layout.addWidget(version)
        
        layout.addWidget(status_bar)
    
    def load_demo_data(self):
        """加载演示数据"""
        self.profile_bar.set_user({
            'nickname': '玩家小明',
            'avatar': '😎',
            'coins': 1680
        })
        
        self.friends_widget.set_friends([
            {'user_id': '1', 'nickname': '游戏达人', 'avatar': '🎮', 'is_online': True, 'in_game': True, 'current_game': '五子棋'},
            {'user_id': '2', 'nickname': '神枪手', 'avatar': '🔫', 'is_online': True},
            {'user_id': '3', 'nickname': '策略大师', 'avatar': '🧠', 'is_online': True},
            {'user_id': '4', 'nickname': '速度之王', 'avatar': '🏎️', 'is_online': False},
            {'user_id': '5', 'nickname': '休闲玩家', 'avatar': '☕', 'is_online': False},
        ])
        
        self.rooms_widget.set_rooms([
            {'room_id': '1001', 'name': '新手友好局', 'game_type': 'gomoku', 'current_players': 1, 'max_players': 2, 'host_name': '小白'},
            {'room_id': '1002', 'name': '激烈对战', 'game_type': 'shooter2d', 'current_players': 5, 'max_players': 8, 'host_name': '枪神'},
            {'room_id': '1003', 'name': '狼人杀欢乐局', 'game_type': 'werewolf', 'current_players': 8, 'max_players': 12, 'host_name': '预言家'},
            {'room_id': '1004', 'name': '大富翁挑战', 'game_type': 'monopoly', 'current_players': 3, 'max_players': 4, 'host_name': '富豪'},
            {'room_id': '1005', 'name': '极速漂移', 'game_type': 'racing', 'current_players': 4, 'max_players': 6, 'host_name': '车神', 'is_playing': True},
        ])
        
        self.chat_widget.set_local_user('self')
        self.chat_widget.add_message({
            'sender_id': '1',
            'sender_name': '游戏达人',
            'sender_color': '#10B981',
            'content': '大家好！有人一起玩五子棋吗？',
            'time': '14:30'
        })
        self.chat_widget.add_message({
            'sender_id': '2',
            'sender_name': '神枪手',
            'sender_color': '#EF4444',
            'content': '我要开一局射击，来吗？',
            'time': '14:31'
        })
        
        # 演示：填充一个示例渲染数据
        demo_state = {
            "game": "gomoku",
            "board_size": 15,
            "current_player": "black",
            "last_move": [7, 7],
            "history_count": 12,
            "status": "等待开始（演示数据）"
        }
        self.set_game_render_data("演示：五子棋", demo_state)
    
    def set_connection_status(self, connected: bool, text: str = ""):
        if connected:
            self.connection_status.setText(f"🟢 {text or '已连接服务器'}")
            self.connection_status.setStyleSheet(f"font-size: 11px; color: {t.success};")
        else:
            self.connection_status.setText(f"🔴 {text or '连接断开'}")
            self.connection_status.setStyleSheet(f"font-size: 11px; color: {t.error};")

    def set_game_render_data(self, title: str, data: dict):
        """更新游戏画面展示（接收插件 render 输出）"""
        if hasattr(self, "game_view"):
            self.game_view.set_render_data(title, data)
