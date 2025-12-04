"""
房间列表组件 - 2.0 设计升级
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor

from ..styles.theme import CURRENT_THEME as t
from ..utils.animation import AnimationUtils


class RoomCard(QWidget):
    """房间卡片"""
    
    join_clicked = Signal(str)  # room_id
    
    def __init__(self, room_data, parent=None):
        super().__init__(parent)
        self.room_data = room_data
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedHeight(88)
        self.setCursor(Qt.PointingHandCursor)
        
        # 外层容器 (用于动效)
        self.container = QFrame(self)
        self.container.setObjectName("roomCard")
        self.container.setGeometry(0, 0, 0, 0) # 稍后在 resizeEvent 中调整
        self.container.setStyleSheet(f"""
            #roomCard {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
            #roomCard:hover {{
                border-color: {t.primary};
                background-color: {t.bg_hover};
            }}
        """)
        
        # 布局
        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(16)
        
        room = self.room_data
        game_type = room.get('game_type', 'unknown')
        
        # 游戏配置
        configs = {
            'gomoku':    {'color': '#10B981', 'icon': '⚫', 'bg': '#ECFDF5'},
            'shooter2d': {'color': '#EF4444', 'icon': '🔫', 'bg': '#FEF2F2'},
            'werewolf':  {'color': '#8B5CF6', 'icon': '🐺', 'bg': '#F5F3FF'},
            'monopoly':  {'color': '#F59E0B', 'icon': '🎲', 'bg': '#FFFBEB'},
            'racing':    {'color': '#06B6D4', 'icon': '🏎️', 'bg': '#ECFEFF'}
        }
        cfg = configs.get(game_type, {'color': '#94A3B8', 'icon': '🎮', 'bg': '#F1F5F9'})
        
        # 图标 (带背景圆)
        icon_box = QLabel()
        icon_box.setFixedSize(48, 48)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setStyleSheet(f"""
            background-color: {cfg['bg']};
            border-radius: 16px;
        """)
        
        icon = QLabel(cfg['icon'])
        icon.setParent(icon_box)
        icon.setStyleSheet("font-size: 24px; background: transparent;")
        icon.move(12, 10) # 微调
        
        layout.addWidget(icon_box)
        
        # 信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignVCenter)
        
        name = QLabel(room.get('name', '未命名房间'))
        name.setProperty("class", "h2")
        name.setStyleSheet("font-size: 15px;")
        info_layout.addWidget(name)
        
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(8)
        
        # 标签样式
        def create_tag(text, color, bg):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"""
                font-size: 11px; color: {color}; background-color: {bg};
                padding: 2px 6px; border-radius: 4px; font-weight: 600;
            """)
            return lbl
            
        tags_layout.addWidget(create_tag(game_type.capitalize(), cfg['color'], cfg['bg']))
        
        current = room.get('current_players', 0)
        max_p = room.get('max_players', 8)
        tags_layout.addWidget(create_tag(f"{current}/{max_p} 人", t.text_caption, t.bg_base))
        
        host = QLabel(f"👑 {room.get('host_name', 'System')}")
        host.setProperty("class", "caption")
        tags_layout.addWidget(host)
        tags_layout.addStretch()
        
        info_layout.addLayout(tags_layout)
        layout.addLayout(info_layout, 1)
        
        # 按钮
        join_btn = QPushButton("加入")
        join_btn.setFixedSize(64, 32)
        join_btn.setCursor(Qt.PointingHandCursor)
        join_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.bg_card};
                color: {cfg['color']};
                border: 1px solid {cfg['color']};
                border-radius: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {cfg['color']};
                color: #FFFFFF;
            }}
        """)
        join_btn.clicked.connect(lambda: self.join_clicked.emit(room.get('room_id')))
        layout.addWidget(join_btn)

    def resizeEvent(self, event):
        self.container.resize(self.width(), self.height())
        super().resizeEvent(event)


class RoomsWidget(QWidget):
    """房间列表面板"""
    
    join_room = Signal(str)
    create_room = Signal()
    quick_match = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rooms_data = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 头部
        header = QHBoxLayout()
        title = QLabel("房间大厅")
        title.setProperty("class", "h2")
        header.addWidget(title)
        header.addStretch()
        
        quick_btn = QPushButton("⚡ 快速匹配")
        quick_btn.setCursor(Qt.PointingHandCursor)
        quick_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.warning}; color: white; border: none;
            }}
            QPushButton:hover {{ background-color: #D97706; }}
        """)
        quick_btn.clicked.connect(self.quick_match.emit)
        header.addWidget(quick_btn)
        
        create_btn = QPushButton("+ 创建")
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.setProperty("class", "primary")
        create_btn.clicked.connect(self.create_room.emit)
        header.addWidget(create_btn)
        
        layout.addLayout(header)
        
        # 滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.container = QWidget()
        self.rooms_layout = QVBoxLayout(self.container)
        self.rooms_layout.setContentsMargins(0, 0, 10, 0) # 右侧留给滚动条
        self.rooms_layout.setSpacing(12)
        self.rooms_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll, 1)
        
        self._refresh_list()

    def set_rooms(self, rooms):
        self.rooms_data = rooms
        self._refresh_list()

    def _refresh_list(self):
        while self.rooms_layout.count() > 1: # 保留 stretch
            item = self.rooms_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        if not self.rooms_data:
            empty = QLabel("暂无房间，快来创建吧！")
            empty.setAlignment(Qt.AlignCenter)
            empty.setProperty("class", "caption")
            empty.setStyleSheet("padding: 40px;")
            self.rooms_layout.insertWidget(0, empty)
        else:
            for i, room in enumerate(self.rooms_data):
                card = RoomCard(room)
                card.join_clicked.connect(self.join_room.emit)
                self.rooms_layout.insertWidget(i, card)
                
                # 列表依次滑入动画
                AnimationUtils.slide_in_up(card, 300, 20 + i*30)
