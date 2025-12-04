"""
好友列表组件 - 修复布局
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal
from typing import List, Dict, Any

from ..styles.theme import CURRENT_THEME as t


class FriendItem(QWidget):
    """好友项 - 修复对齐"""
    
    invite_clicked = Signal(str)
    
    def __init__(self, user_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setFixedHeight(68)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        user = self.user_data
        is_online = user.get('is_online', False)
        
        # 头像容器 - 固定尺寸
        avatar_container = QWidget()
        avatar_container.setFixedSize(44, 44)
        
        # 头像背景
        avatar_bg = QFrame(avatar_container)
        avatar_bg.setGeometry(0, 0, 44, 44)
        avatar_bg.setStyleSheet(f"""
            background-color: {t.bg_base};
            border-radius: 22px;
        """)
        
        # 头像图标
        avatar_icon = QLabel(user.get('avatar', '👤'), avatar_container)
        avatar_icon.setGeometry(0, 0, 44, 44)
        avatar_icon.setAlignment(Qt.AlignCenter)
        avatar_icon.setStyleSheet("font-size: 22px; background: transparent;")
        
        # 在线状态点 - 精确定位
        if is_online:
            status_dot = QFrame(avatar_container)
            status_dot.setGeometry(32, 32, 12, 12)
            status_dot.setStyleSheet(f"""
                background-color: {t.success};
                border: 2px solid white;
                border-radius: 6px;
            """)
        
        layout.addWidget(avatar_container)
        
        # 信息区
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignVCenter)
        
        # 昵称
        name = QLabel(user.get('nickname', 'Unknown'))
        name.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {t.text_display};
        """)
        info_layout.addWidget(name)
        
        # 状态
        status_text = "🟢 在线" if is_online else "⚫ 离线"
        status_color = t.success if is_online else t.text_caption
        
        if user.get('in_game'):
            status_text = f"🎮 {user.get('current_game', '游戏中')}"
            status_color = t.secondary
        
        status = QLabel(status_text)
        status.setStyleSheet(f"""
            font-size: 12px;
            color: {status_color};
        """)
        info_layout.addWidget(status)
        
        layout.addLayout(info_layout, 1)
        
        # 邀请按钮
        if is_online:
            invite_btn = QPushButton("邀请")
            invite_btn.setFixedSize(52, 28)
            invite_btn.setCursor(Qt.PointingHandCursor)
            invite_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t.primary_bg};
                    color: {t.primary};
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: #DBEAFE;
                }}
            """)
            invite_btn.clicked.connect(lambda: self.invite_clicked.emit(user.get('user_id', '')))
            layout.addWidget(invite_btn)


class FriendsWidget(QWidget):
    """好友列表"""
    
    invite_friend = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.friends_data: List[Dict] = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 头部
        header = QHBoxLayout()
        
        title = QLabel("好友")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {t.text_display};")
        header.addWidget(title)
        
        header.addStretch()
        
        self.online_count = QLabel("0 在线")
        self.online_count.setStyleSheet(f"font-size: 12px; color: {t.success}; font-weight: 500;")
        header.addWidget(self.online_count)
        
        # 添加按钮
        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.bg_base};
                color: {t.text_caption};
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
                color: {t.primary};
            }}
        """)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索好友...")
        self.search_input.setFixedHeight(36)
        layout.addWidget(self.search_input)
        
        # 好友列表容器
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 4, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()
        
        layout.addWidget(self.container, 1)

    def set_friends(self, friends: List[Dict[str, Any]]):
        self.friends_data = friends
        self._refresh_list()

    def _refresh_list(self):
        # 清空
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.friends_data:
            empty = QLabel("暂无好友")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {t.text_caption}; padding: 20px;")
            self.list_layout.insertWidget(0, empty)
            self.online_count.setText("0 在线")
            return
        
        # 在线排前
        online = [f for f in self.friends_data if f.get('is_online')]
        offline = [f for f in self.friends_data if not f.get('is_online')]
        
        self.online_count.setText(f"{len(online)} 在线")
        
        # 显示在线好友
        if online:
            online_header = QLabel("在线")
            online_header.setStyleSheet(f"""
                font-size: 11px;
                color: {t.text_caption};
                padding: 8px 12px 4px;
                font-weight: 600;
            """)
            self.list_layout.insertWidget(self.list_layout.count() - 1, online_header)
            
            for f in online:
                item = FriendItem(f)
                item.invite_clicked.connect(self.invite_friend.emit)
                self.list_layout.insertWidget(self.list_layout.count() - 1, item)
        
        # 显示离线好友
        if offline:
            offline_header = QLabel("离线")
            offline_header.setStyleSheet(f"""
                font-size: 11px;
                color: {t.text_caption};
                padding: 12px 12px 4px;
                font-weight: 600;
            """)
            self.list_layout.insertWidget(self.list_layout.count() - 1, offline_header)
            
            for f in offline:
                item = FriendItem(f)
                self.list_layout.insertWidget(self.list_layout.count() - 1, item)
