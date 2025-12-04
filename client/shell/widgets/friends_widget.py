"""
好友列表组件 - 现代化浅色风格
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
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        user = self.user_data
        is_online = user.get('is_online', False)
        
        # 头像容器
        avatar_container = QWidget()
        avatar_container.setFixedSize(40, 40)
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        
        avatar_label = QLabel(user.get('avatar', '👤'))
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setStyleSheet("""
            background-color: #F3F4F6;
            border-radius: 20px;
            font-size: 20px;
        """)
        avatar_label.setFixedSize(40, 40)
        avatar_layout.addWidget(avatar_label)
        
        # 在线状态点
        status_color = '#10B981' if is_online else '#9CA3AF'
        status_dot = QLabel()
        status_dot.setFixedSize(10, 10)
        status_dot.setStyleSheet(f"""
            background-color: {status_color};
            border-radius: 5px;
            border: 2px solid #FFFFFF;
        """)
        status_dot.setParent(avatar_container)
        status_dot.move(28, 28)
        
        layout.addWidget(avatar_container)
        
        # 用户信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # 昵称
        name_label = QLabel(user.get('nickname', '未知用户'))
        name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #111827;
        """)
        info_layout.addWidget(name_label)
        
        # 状态文字
        status_text = user.get('status', '在线' if is_online else '离线')
        if user.get('in_game'):
            status_text = f"🎮 {user.get('current_game', '游戏中')}"
            
        status_label = QLabel(status_text)
        status_color = '#10B981' if is_online else '#9CA3AF'
        if user.get('in_game'):
            status_color = '#F59E0B'
            
        status_label.setStyleSheet(f"""
            font-size: 12px;
            color: {status_color};
        """)
        info_layout.addWidget(status_label)
        
        layout.addLayout(info_layout, 1)
        
        # 操作按钮
        if is_online:
            invite_btn = QPushButton("邀请")
            invite_btn.setFixedSize(50, 26)
            invite_btn.setCursor(Qt.PointingHandCursor)
            invite_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EFF6FF;
                    color: #2563EB;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #DBEAFE;
                }
            """)
            invite_btn.clicked.connect(
                lambda: self.invite_clicked.emit(user.get('user_id', ''))
            )
            layout.addWidget(invite_btn)


class FriendsWidget(QWidget):
    """好友列表面板"""
    
    invite_friend = Signal(str)
    chat_with = Signal(str)
    
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
        
        title = QLabel("好友")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #111827;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.online_count = QLabel("0 在线")
        self.online_count.setStyleSheet("font-size: 12px; color: #10B981; font-weight: 500;")
        header.addWidget(self.online_count)
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #4B5563;
                border: none;
                border-radius: 6px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
                color: #111827;
            }
        """)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索好友...")
        # 样式使用全局 QSS
        layout.addWidget(self.search_input)
        
        # 列表容器
        self.list_container = QFrame()
        self.list_container.setStyleSheet("background: transparent; border: none;")
        
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 4, 0, 4)
        self.list_layout.setSpacing(2)
        
        self.list_layout.addStretch()
        layout.addWidget(self.list_container, 1)
        
    # set_friends, _refresh_list 等逻辑保持不变，只需更新内部样式
    def set_friends(self, friends: List[Dict[str, Any]]):
        self.friends_data = friends
        self._refresh_list()
    
    def _refresh_list(self):
        while self.list_layout.count() > 0:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.friends_data:
            empty = QLabel("暂无好友")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #9CA3AF; margin-top: 20px;")
            self.list_layout.addWidget(empty)
            self.list_layout.addStretch()
            return
            
        online = [f for f in self.friends_data if f.get('is_online')]
        offline = [f for f in self.friends_data if not f.get('is_online')]
        
        self.online_count.setText(f"{len(online)} 在线")
        
        if online:
            header = QLabel("在线")
            header.setStyleSheet("font-size: 12px; color: #6B7280; padding: 8px 4px; font-weight: 600;")
            self.list_layout.addWidget(header)
            for f in online:
                item = FriendItem(f)
                item.invite_clicked.connect(self.invite_friend.emit)
                self.list_layout.addWidget(item)
                
        if offline:
            header = QLabel("离线")
            header.setStyleSheet("font-size: 12px; color: #6B7280; padding: 12px 4px 8px 4px; font-weight: 600;")
            self.list_layout.addWidget(header)
            for f in offline:
                item = FriendItem(f)
                self.list_layout.addWidget(item)
                
        self.list_layout.addStretch()
