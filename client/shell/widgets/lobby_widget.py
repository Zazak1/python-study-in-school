"""
大厅主界面组件 - 现代化浅色风格
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QScrollArea,
    QGridLayout, QSplitter, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon

from .game_card import GameCard
from .friends_widget import FriendsWidget
from .rooms_widget import RoomsWidget
from .chat_widget import ChatWidget


class UserProfileBar(QWidget):
    """用户信息栏"""
    
    settings_clicked = Signal()
    logout_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data = {}
        self.setup_ui()
    
    def setup_ui(self):
        """设置 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)
        
        # 用户头像
        self.avatar_label = QLabel("👤")
        self.avatar_label.setFixedSize(48, 48)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("""
            background-color: #F3F4F6;
            border-radius: 24px;
            font-size: 24px;
            border: 1px solid #E5E7EB;
        """)
        layout.addWidget(self.avatar_label)
        
        # 用户信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.name_label = QLabel("游客用户")
        self.name_label.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        info_layout.addWidget(self.name_label)
        
        self.status_label = QLabel("🟢 在线")
        self.status_label.setStyleSheet("font-size: 12px; color: #10B981; font-weight: 500;")
        info_layout.addWidget(self.status_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # 货币显示
        coins_frame = QFrame()
        coins_frame.setStyleSheet("""
            QFrame {
                background-color: #EFF6FF;
                border-radius: 8px;
                padding: 4px 12px;
                border: 1px solid #DBEAFE;
            }
        """)
        coins_layout = QHBoxLayout(coins_frame)
        coins_layout.setContentsMargins(12, 6, 12, 6)
        coins_layout.setSpacing(8)
        
        coin_icon = QLabel("💎")
        coin_icon.setStyleSheet("font-size: 14px; background: transparent;")
        coins_layout.addWidget(coin_icon)
        
        self.coins_label = QLabel("0")
        self.coins_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #2563EB; background: transparent;")
        coins_layout.addWidget(self.coins_label)
        
        layout.addWidget(coins_frame)
        
        # 操作按钮
        settings_btn = self._create_icon_btn("⚙️", "设置")
        settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(settings_btn)
        
        logout_btn = self._create_icon_btn("🚪", "退出")
        logout_btn.clicked.connect(self.logout_clicked.emit)
        layout.addWidget(logout_btn)
    
    def _create_icon_btn(self, icon: str, tooltip: str):
        btn = QPushButton(icon)
        btn.setFixedSize(40, 40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(tooltip)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #D1D5DB;
            }
        """)
        return btn
    
    def set_user(self, user_data: dict):
        self.user_data = user_data
        self.name_label.setText(user_data.get('nickname', '游客用户'))
        self.coins_label.setText(str(user_data.get('coins', 0)))
        if user_data.get('avatar'):
            self.avatar_label.setText(user_data['avatar'])


class LobbyWidget(QWidget):
    """大厅主界面"""
    
    # 信号
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
        """设置 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部用户信息栏
        self.profile_bar = UserProfileBar()
        self.profile_bar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E5E7EB;")
        self.profile_bar.logout_clicked.connect(self.logout_requested.emit)
        main_layout.addWidget(self.profile_bar)
        
        # 主内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #F3F4F6;") # 浅灰底色
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(24)
        
        # ========== 左侧面板：游戏选择 + 房间列表 ==========
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(24)
        
        # 游戏选择区域
        games_section = QFrame()
        games_section.setObjectName("card") # 使用通用卡片样式
        games_layout = QVBoxLayout(games_section)
        games_layout.setContentsMargins(24, 24, 24, 24)
        games_layout.setSpacing(16)
        
        # 标题
        games_title = QLabel("选择游戏")
        games_title.setProperty("class", "title")
        games_title.setStyleSheet("font-size: 18px;")
        games_layout.addWidget(games_title)
        
        # 游戏卡片网格
        games_grid = QHBoxLayout()
        games_grid.setSpacing(16)
        
        game_ids = ['gomoku', 'shooter2d', 'werewolf', 'monopoly', 'racing']
        for game_id in game_ids:
            card = GameCard(game_id)
            card.clicked.connect(self.game_selected.emit)
            games_grid.addWidget(card)
        
        games_grid.addStretch()
        games_layout.addLayout(games_grid)
        
        left_layout.addWidget(games_section)
        
        # 房间列表容器 (使用通用卡片样式)
        rooms_container = QFrame()
        rooms_container.setObjectName("card")
        rooms_inner = QVBoxLayout(rooms_container)
        rooms_inner.setContentsMargins(24, 24, 24, 24)
        
        self.rooms_widget = RoomsWidget()
        self.rooms_widget.join_room.connect(self.room_joined.emit)
        self.rooms_widget.create_room.connect(self.room_created.emit)
        self.rooms_widget.quick_match.connect(self.quick_match_requested.emit)
        rooms_inner.addWidget(self.rooms_widget)
        
        left_layout.addWidget(rooms_container, 1)
        
        content_layout.addWidget(left_panel, 3)
        
        # ========== 右侧面板：好友 + 聊天 ==========
        right_panel = QWidget()
        right_panel.setFixedWidth(340)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(24)
        
        # 好友列表
        friends_frame = QFrame()
        friends_frame.setObjectName("card")
        friends_inner = QVBoxLayout(friends_frame)
        friends_inner.setContentsMargins(16, 16, 16, 16)
        
        self.friends_widget = FriendsWidget()
        friends_inner.addWidget(self.friends_widget)
        
        right_layout.addWidget(friends_frame)
        
        # 聊天区域
        chat_frame = QFrame()
        chat_frame.setObjectName("card")
        chat_inner = QVBoxLayout(chat_frame)
        chat_inner.setContentsMargins(16, 16, 16, 16)
        
        self.chat_widget = ChatWidget()
        chat_inner.addWidget(self.chat_widget)
        
        right_layout.addWidget(chat_frame, 1)
        
        content_layout.addWidget(right_panel)
        
        main_layout.addWidget(content_widget, 1)
        
        # 底部状态栏
        status_bar = QFrame()
        status_bar.setFixedHeight(32)
        status_bar.setStyleSheet("background-color: #FFFFFF; border-top: 1px solid #E5E7EB;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(24, 0, 24, 0)
        
        self.connection_status = QLabel("🟢 已连接服务器")
        self.connection_status.setStyleSheet("font-size: 11px; color: #10B981;")
        status_layout.addWidget(self.connection_status)
        
        status_layout.addStretch()
        
        version_label = QLabel("Aether Party v0.1.0")
        version_label.setStyleSheet("font-size: 11px; color: #9CA3AF;")
        status_layout.addWidget(version_label)
        
        main_layout.addWidget(status_bar)

    # load_demo_data 和 set_connection_status 保持不变
    def load_demo_data(self):
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

    def set_connection_status(self, connected: bool, text: str = ""):
        if connected:
            self.connection_status.setText(f"🟢 {text or '已连接服务器'}")
            self.connection_status.setStyleSheet("font-size: 11px; color: #10B981;")
        else:
            self.connection_status.setText(f"🔴 {text or '连接断开'}")
            self.connection_status.setStyleSheet("font-size: 11px; color: #EF4444;")
