"""
好友列表组件 - 2.0 设计升级
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation
from PySide6.QtGui import QColor

from ..styles.theme import CURRENT_THEME as t


class FriendItem(QWidget):
    """好友项"""
    
    invite_clicked = Signal(str)
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(64)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        user = self.user_data
        is_online = user.get('is_online', False)
        
        # 头像容器
        avatar_box = QWidget()
        avatar_box.setFixedSize(44, 44)
        
        # 头像
        avatar = QLabel(user.get('avatar', '👤'))
        avatar.setParent(avatar_box)
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {t.bg_base};
            border-radius: 22px;
            font-size: 22px;
        """)
        
        # 在线状态 (呼吸灯)
        if is_online:
            dot = QLabel()
            dot.setParent(avatar_box)
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"""
                background-color: {t.success};
                border: 2px solid #FFFFFF;
                border-radius: 6px;
            """)
            dot.move(32, 32)
            
            # 呼吸动画 (可选)
            # anim = QPropertyAnimation(...)
        
        layout.addWidget(avatar_box)
        
        # 信息
        info = QVBoxLayout()
        info.setSpacing(2)
        info.setAlignment(Qt.AlignVCenter)
        
        name = QLabel(user.get('nickname', 'Unknown'))
        name.setStyleSheet(f"font-weight: 600; color: {t.text_display}; font-size: 14px;")
        info.addWidget(name)
        
        status_txt = "在线" if is_online else "离线"
        status_color = t.success if is_online else t.text_caption
        if user.get('in_game'):
            status_txt = f"正在玩 {user.get('current_game')}"
            status_color = t.secondary
            
        status = QLabel(status_txt)
        status.setStyleSheet(f"font-size: 11px; color: {status_color};")
        info.addWidget(status)
        
        layout.addLayout(info, 1)
        
        # 邀请按钮 (悬停显示)
        if is_online:
            btn = QPushButton("邀请")
            btn.setFixedSize(48, 26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t.primary_bg};
                    color: {t.primary};
                    border: none;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{ background-color: #DBEAFE; }}
            """)
            btn.clicked.connect(lambda: self.invite_clicked.emit(user.get('user_id')))
            layout.addWidget(btn)


class FriendsWidget(QWidget):
    """好友列表"""
    
    invite_friend = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.friends_data = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 头
        header = QHBoxLayout()
        title = QLabel("好友")
        title.setProperty("class", "h2")
        header.addWidget(title)
        header.addStretch()
        
        self.count = QLabel("0/0")
        self.count.setProperty("class", "caption")
        header.addWidget(self.count)
        
        layout.addLayout(header)
        
        # 列表
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()
        
        layout.addWidget(self.container, 1)
        
    def set_friends(self, friends):
        self.friends_data = friends
        self._refresh()
        
    def _refresh(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        online = [f for f in self.friends_data if f.get('is_online')]
        self.count.setText(f"{len(online)}/{len(self.friends_data)}")
        
        # 先在线后离线
        sorted_friends = sorted(self.friends_data, key=lambda x: not x.get('is_online'))
        
        for f in sorted_friends:
            item = FriendItem(f)
            item.invite_clicked.connect(self.invite_friend.emit)
            self.list_layout.insertWidget(self.list_layout.count()-1, item)
