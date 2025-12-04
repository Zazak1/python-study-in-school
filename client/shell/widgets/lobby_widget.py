"""
大厅主界面组件 - 2.0 设计升级
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QStackedWidget, QScrollArea,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from .game_card import GameCard
from .friends_widget import FriendsWidget
from .rooms_widget import RoomsWidget
from .chat_widget import ChatWidget
from ..utils.animation import AnimationUtils
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
        
        # 头像
        self.avatar_label = QLabel("👤")
        self.avatar_label.setFixedSize(48, 48)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet(f"""
            background-color: {t.bg_base};
            border-radius: 24px;
            font-size: 24px;
            border: 2px solid {t.bg_card};
        """)
        # 添加阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.avatar_label.setGraphicsEffect(shadow)
        layout.addWidget(self.avatar_label)
        
        # 信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        self.name_label = QLabel("游客用户")
        self.name_label.setProperty("class", "h2")
        info_layout.addWidget(self.name_label)
        
        status_layout = QHBoxLayout()
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {t.success}; font-size: 10px;")
        self.status_label = QLabel("在线")
        self.status_label.setProperty("class", "caption")
        status_layout.addWidget(status_dot)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        info_layout.addLayout(status_layout)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # 货币
        coins_btn = QPushButton()
        coins_btn.setCursor(Qt.PointingHandCursor)
        coins_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.primary_bg};
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                text-align: left;
            }}
            QPushButton:hover {{ background-color: #DBEAFE; }}
        """)
        coins_layout = QHBoxLayout(coins_btn)
        coins_layout.setContentsMargins(4, 0, 4, 0)
        
        coin_icon = QLabel("💎")
        self.coins_label = QLabel("0")
        self.coins_label.setStyleSheet(f"color: {t.primary}; font-weight: 700; font-size: 14px;")
        
        coins_layout.addWidget(coin_icon)
        coins_layout.addWidget(self.coins_label)
        layout.addWidget(coins_btn)
        
        # 按钮
        settings_btn = self._create_icon_btn("⚙️", "设置")
        settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(settings_btn)
        
        logout_btn = self._create_icon_btn("🚪", "退出")
        logout_btn.clicked.connect(self.logout_clicked.emit)
        layout.addWidget(logout_btn)
        
    def _create_icon_btn(self, icon, tooltip):
        btn = QPushButton(icon)
        btn.setProperty("class", "icon-btn")
        btn.setFixedSize(40, 40)
        btn.setToolTip(tooltip)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 20px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                border-color: {t.primary};
                color: {t.primary};
                background-color: {t.bg_hover};
            }}
        """)
        return btn

    def set_user(self, user_data):
        self.name_label.setText(user_data.get('nickname', '游客'))
        self.coins_label.setText(str(user_data.get('coins', 0)))
        if user_data.get('avatar'):
            self.avatar_label.setText(user_data['avatar'])


class LobbyWidget(QWidget):
    """大厅主界面"""
    
    # 信号保持不变
    game_selected = Signal(str)
    room_joined = Signal(str)
    room_created = Signal()
    quick_match_requested = Signal()
    logout_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_demo_data()
        
        # 入场动画
        AnimationUtils.fade_in(self, 500)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 顶部栏
        self.profile_bar = UserProfileBar()
        self.profile_bar.setStyleSheet(f"background-color: {t.bg_card}; border-bottom: 1px solid {t.border_light};")
        self.profile_bar.logout_clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.profile_bar)
        
        # 内容区 (带背景色)
        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {t.bg_base};")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(32, 32, 32, 32)
        content_layout.setSpacing(24)
        
        # 左侧：游戏 + 房间
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(24)
        
        # 1. 游戏选择 (透明背景，不使用卡片容器，直接展示卡片)
        games_header = QLabel("开始游戏")
        games_header.setProperty("class", "h2")
        left_layout.addWidget(games_header)
        
        games_grid = QHBoxLayout()
        games_grid.setSpacing(20)
        
        game_ids = ['gomoku', 'shooter2d', 'werewolf', 'monopoly', 'racing']
        for i, game_id in enumerate(game_ids):
            card = GameCard(game_id)
            card.clicked.connect(self.game_selected.emit)
            games_grid.addWidget(card)
            
            # 依次入场动画
            AnimationUtils.slide_in_up(card, 400, 20 + i*10)
            
        games_grid.addStretch()
        left_layout.addLayout(games_grid)
        
        # 2. 房间列表 (卡片容器)
        rooms_frame = QFrame()
        rooms_frame.setObjectName("card")
        rooms_layout = QVBoxLayout(rooms_frame)
        rooms_layout.setContentsMargins(0, 0, 0, 0)
        
        self.rooms_widget = RoomsWidget()
        self.rooms_widget.join_room.connect(self.room_joined.emit)
        self.rooms_widget.create_room.connect(self.room_created.emit)
        self.rooms_widget.quick_match.connect(self.quick_match_requested.emit)
        # 移除 RoomsWidget 内部的边距，由 Frame 控制
        self.rooms_widget.layout().setContentsMargins(24, 24, 24, 24)
        
        rooms_layout.addWidget(self.rooms_widget)
        left_layout.addWidget(rooms_frame, 1)
        
        content_layout.addWidget(left_panel, 1) # 左侧占宽比
        
        # 右侧：社交 (卡片容器)
        right_panel = QWidget()
        right_panel.setFixedWidth(360)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(24)
        
        # 好友
        friends_frame = QFrame()
        friends_frame.setObjectName("card")
        friends_inner = QVBoxLayout(friends_frame)
        friends_inner.setContentsMargins(20, 20, 20, 20)
        
        self.friends_widget = FriendsWidget()
        friends_inner.addWidget(self.friends_widget)
        right_layout.addWidget(friends_frame, 1)
        
        # 聊天
        chat_frame = QFrame()
        chat_frame.setObjectName("card")
        chat_inner = QVBoxLayout(chat_frame)
        chat_inner.setContentsMargins(20, 20, 20, 20)
        
        self.chat_widget = ChatWidget()
        chat_inner.addWidget(self.chat_widget)
        right_layout.addWidget(chat_frame, 2)
        
        content_layout.addWidget(right_panel)
        
        layout.addWidget(content_widget, 1)
        
        # 底部状态栏
        self._setup_status_bar(layout)
        
    def _setup_status_bar(self, layout):
        status_bar = QFrame()
        status_bar.setFixedHeight(32)
        status_bar.setStyleSheet(f"background-color: {t.bg_card}; border-top: 1px solid {t.border_light};")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(32, 0, 32, 0)
        
        self.connection_status = QLabel("🟢 已连接服务器")
        self.connection_status.setProperty("class", "caption")
        self.connection_status.setStyleSheet(f"color: {t.success};")
        status_layout.addWidget(self.connection_status)
        
        status_layout.addStretch()
        
        version = QLabel("Aether Party v0.1.0")
        version.setProperty("class", "caption")
        status_layout.addWidget(version)
        
        layout.addWidget(status_bar)

    def load_demo_data(self):
        self.profile_bar.set_user({'nickname': '设计体验官', 'avatar': '👨‍🎨', 'coins': 8888})
        # ... 其他数据保持不变 ... (略，节省篇幅，实际代码需保留)
        # 这里为了完整性，快速填充一下
        self.friends_widget.set_friends([
            {'user_id': '1', 'nickname': 'UI 大师', 'avatar': '🎨', 'is_online': True},
            {'user_id': '2', 'nickname': '代码猎手', 'avatar': '💻', 'is_online': True, 'in_game': True, 'current_game': '2D射击'},
        ])
        self.rooms_widget.set_rooms([
            {'room_id': '1', 'name': '设计交流会', 'game_type': 'gomoku', 'current_players': 1, 'max_players': 2, 'host_name': 'Admin'},
            {'room_id': '2', 'name': '午休摸鱼', 'game_type': 'shooter2d', 'current_players': 3, 'max_players': 6, 'host_name': 'Boss'},
        ])
        self.chat_widget.set_local_user('self')
        self.chat_widget.add_message({'sender_id': '1', 'sender_name': 'UI 大师', 'content': '新界面真不错！', 'time': '10:00'})
        
    def set_connection_status(self, connected: bool, text: str = ""):
        if connected:
            self.connection_status.setText(f"🟢 {text or '已连接服务器'}")
            self.connection_status.setStyleSheet(f"color: {t.success};")
        else:
            self.connection_status.setText(f"🔴 {text or '连接断开'}")
            self.connection_status.setStyleSheet(f"color: {t.error};")
