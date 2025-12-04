"""
好友列表组件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QAction
from typing import List, Dict, Any


class FriendItem(QWidget):
    """好友列表项"""
    
    invite_clicked = Signal(str)  # user_id
    chat_clicked = Signal(str)    # user_id
    
    def __init__(self, user_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setup_ui()
    
    def setup_ui(self):
        """设置 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        user = self.user_data
        is_online = user.get('is_online', False)
        
        # 头像 + 状态指示
        avatar_container = QWidget()
        avatar_container.setFixedSize(44, 44)
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        avatar_label = QLabel(user.get('avatar', '👤'))
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setStyleSheet("""
            background: #1F2937;
            border-radius: 22px;
            font-size: 22px;
        """)
        avatar_label.setFixedSize(44, 44)
        avatar_layout.addWidget(avatar_label)
        
        # 在线状态点
        status_color = '#10B981' if is_online else '#64748B'
        status_dot = QLabel()
        status_dot.setFixedSize(12, 12)
        status_dot.setStyleSheet(f"""
            background: {status_color};
            border-radius: 6px;
            border: 2px solid #161E2E;
        """)
        status_dot.move(32, 32)
        status_dot.setParent(avatar_container)
        
        layout.addWidget(avatar_container)
        
        # 用户信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # 昵称
        name_label = QLabel(user.get('nickname', '未知用户'))
        name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #F0F4F8;
            background: transparent;
        """)
        info_layout.addWidget(name_label)
        
        # 状态文字
        status_text = user.get('status', '在线' if is_online else '离线')
        if user.get('in_game'):
            status_text = f"🎮 {user.get('current_game', '游戏中')}"
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            font-size: 12px;
            color: {'#10B981' if is_online else '#64748B'};
            background: transparent;
        """)
        info_layout.addWidget(status_label)
        
        layout.addLayout(info_layout, 1)
        
        # 操作按钮（仅在线时显示）
        if is_online:
            invite_btn = QPushButton("邀请")
            invite_btn.setFixedSize(60, 28)
            invite_btn.setCursor(Qt.PointingHandCursor)
            invite_btn.setStyleSheet("""
                QPushButton {
                    background: #00D4FF;
                    color: #0A0E17;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #5CE1FF;
                }
            """)
            invite_btn.clicked.connect(
                lambda: self.invite_clicked.emit(user.get('user_id', ''))
            )
            layout.addWidget(invite_btn)


class FriendsWidget(QWidget):
    """好友列表面板"""
    
    invite_friend = Signal(str)  # user_id
    chat_with = Signal(str)      # user_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.friends_data: List[Dict] = []
        self.setup_ui()
    
    def setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 标题栏
        header = QHBoxLayout()
        
        title = QLabel("👥 好友")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #F0F4F8;
            background: transparent;
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # 在线数量
        self.online_count = QLabel("0 在线")
        self.online_count.setStyleSheet("""
            font-size: 12px;
            color: #10B981;
            background: transparent;
        """)
        header.addWidget(self.online_count)
        
        # 添加好友按钮
        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 28)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolTip("添加好友")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #2d3748;
                color: #00D4FF;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #00D4FF;
                color: #0A0E17;
            }
        """)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索好友...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #1F2937;
                border: 1px solid #2d3748;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #F0F4F8;
            }
            QLineEdit:focus {
                border-color: #00D4FF;
            }
        """)
        self.search_input.textChanged.connect(self._filter_friends)
        layout.addWidget(self.search_input)
        
        # 好友列表容器
        self.list_container = QFrame()
        self.list_container.setStyleSheet("""
            QFrame {
                background: #111827;
                border: 1px solid #2d3748;
                border-radius: 8px;
            }
        """)
        
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(4, 4, 4, 4)
        self.list_layout.setSpacing(2)
        
        # 空状态提示
        self.empty_label = QLabel("暂无好友\n点击 + 添加好友")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            color: #64748B;
            font-size: 13px;
            padding: 40px;
            background: transparent;
        """)
        self.list_layout.addWidget(self.empty_label)
        
        self.list_layout.addStretch()
        
        layout.addWidget(self.list_container, 1)
    
    def set_friends(self, friends: List[Dict[str, Any]]):
        """设置好友数据"""
        self.friends_data = friends
        self._refresh_list()
    
    def _refresh_list(self):
        """刷新好友列表"""
        # 清空现有项
        while self.list_layout.count() > 0:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.friends_data:
            self.empty_label = QLabel("暂无好友\n点击 + 添加好友")
            self.empty_label.setAlignment(Qt.AlignCenter)
            self.empty_label.setStyleSheet("""
                color: #64748B;
                font-size: 13px;
                padding: 40px;
                background: transparent;
            """)
            self.list_layout.addWidget(self.empty_label)
            self.list_layout.addStretch()
            self.online_count.setText("0 在线")
            return
        
        # 分离在线和离线好友
        online = [f for f in self.friends_data if f.get('is_online')]
        offline = [f for f in self.friends_data if not f.get('is_online')]
        
        # 更新在线数量
        self.online_count.setText(f"{len(online)} 在线")
        
        # 添加在线好友
        if online:
            online_header = QLabel("在线")
            online_header.setStyleSheet("""
                font-size: 11px;
                color: #64748B;
                padding: 8px 12px 4px 12px;
                background: transparent;
            """)
            self.list_layout.addWidget(online_header)
            
            for friend in online:
                item = FriendItem(friend)
                item.invite_clicked.connect(self.invite_friend.emit)
                item.chat_clicked.connect(self.chat_with.emit)
                self.list_layout.addWidget(item)
        
        # 添加离线好友
        if offline:
            offline_header = QLabel("离线")
            offline_header.setStyleSheet("""
                font-size: 11px;
                color: #64748B;
                padding: 12px 12px 4px 12px;
                background: transparent;
            """)
            self.list_layout.addWidget(offline_header)
            
            for friend in offline:
                item = FriendItem(friend)
                item.chat_clicked.connect(self.chat_with.emit)
                self.list_layout.addWidget(item)
        
        self.list_layout.addStretch()
    
    def _filter_friends(self, text: str):
        """过滤好友列表"""
        if not text:
            self._refresh_list()
            return
        
        text = text.lower()
        filtered = [
            f for f in self.friends_data 
            if text in f.get('nickname', '').lower()
        ]
        
        # 临时显示过滤结果
        while self.list_layout.count() > 0:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for friend in filtered:
            item = FriendItem(friend)
            item.invite_clicked.connect(self.invite_friend.emit)
            self.list_layout.addWidget(item)
        
        self.list_layout.addStretch()

