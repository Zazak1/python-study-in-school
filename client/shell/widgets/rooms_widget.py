"""
房间列表组件 - 修复布局
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import List, Dict, Any

from ..styles.theme import CURRENT_THEME as t
from ..utils.animation import AnimationUtils


class RoomCard(QWidget):
    """房间卡片 - 修复尺寸和对齐"""
    
    join_clicked = Signal(str)
    
    def __init__(self, room_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.room_data = room_data
        self.setFixedHeight(88)
        self.setup_ui()
    
    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 卡片容器
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {t.primary};
                background-color: {t.bg_hover};
            }}
        """)
        
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(16)
        
        room = self.room_data
        game_type = room.get('game_type', 'unknown')
        
        # 游戏配置
        configs = {
            'gomoku':    {'color': '#10B981', 'icon': '⚫', 'bg': '#ECFDF5', 'name': '五子棋'},
            'shooter2d': {'color': '#EF4444', 'icon': '🔫', 'bg': '#FEF2F2', 'name': '2D射击'},
            'werewolf':  {'color': '#8B5CF6', 'icon': '🐺', 'bg': '#F5F3FF', 'name': '狼人杀'},
            'monopoly':  {'color': '#F59E0B', 'icon': '🎲', 'bg': '#FFFBEB', 'name': '大富翁'},
            'racing':    {'color': '#06B6D4', 'icon': '🏎️', 'bg': '#ECFEFF', 'name': '赛车'}
        }
        cfg = configs.get(game_type, {'color': '#94A3B8', 'icon': '🎮', 'bg': '#F1F5F9', 'name': '未知'})
        
        # 图标容器 - 固定尺寸
        icon_container = QWidget()
        icon_container.setFixedSize(48, 48)
        
        icon_bg = QFrame(icon_container)
        icon_bg.setGeometry(0, 0, 48, 48)
        icon_bg.setStyleSheet(f"""
            background-color: {cfg['bg']};
            border-radius: 12px;
        """)
        
        icon = QLabel(cfg['icon'], icon_container)
        icon.setGeometry(0, 0, 48, 48)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 24px; background: transparent;")
        
        card_layout.addWidget(icon_container)
        
        # 信息区
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignVCenter)
        
        # 房间名
        name_label = QLabel(room.get('name', f'房间 {room.get("room_id", "?")}'))
        name_label.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 600;
            color: {t.text_display};
        """)
        info_layout.addWidget(name_label)
        
        # 标签行
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(8)
        
        # 游戏类型标签
        game_tag = QLabel(cfg['name'])
        game_tag.setStyleSheet(f"""
            font-size: 11px;
            color: {cfg['color']};
            background-color: {cfg['bg']};
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        """)
        tags_layout.addWidget(game_tag)
        
        # 人数
        current = room.get('current_players', 0)
        max_p = room.get('max_players', 8)
        players_tag = QLabel(f"{current}/{max_p}人")
        players_tag.setStyleSheet(f"""
            font-size: 11px;
            color: {t.text_caption};
            background-color: {t.bg_base};
            padding: 2px 8px;
            border-radius: 4px;
        """)
        tags_layout.addWidget(players_tag)
        
        # 房主
        host_label = QLabel(f"👑 {room.get('host_name', 'System')}")
        host_label.setStyleSheet(f"font-size: 11px; color: {t.text_caption};")
        tags_layout.addWidget(host_label)
        
        tags_layout.addStretch()
        info_layout.addLayout(tags_layout)
        
        card_layout.addLayout(info_layout, 1)
        
        # 操作按钮
        is_playing = room.get('is_playing', False)
        is_full = current >= max_p
        
        if is_playing:
            status = QLabel("游戏中")
            status.setStyleSheet(f"""
                font-size: 12px;
                color: {t.warning};
                background-color: {t.bg_base};
                padding: 6px 12px;
                border-radius: 8px;
                font-weight: 500;
            """)
            card_layout.addWidget(status)
        elif is_full:
            status = QLabel("已满")
            status.setStyleSheet(f"""
                font-size: 12px;
                color: {t.error};
                background-color: #FEF2F2;
                padding: 6px 12px;
                border-radius: 8px;
                font-weight: 500;
            """)
            card_layout.addWidget(status)
        else:
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
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {cfg['color']};
                    color: white;
                }}
            """)
            join_btn.clicked.connect(lambda: self.join_clicked.emit(room.get('room_id', '')))
            card_layout.addWidget(join_btn)
        
        layout.addWidget(card)


class RoomsWidget(QWidget):
    """房间列表面板"""
    
    join_room = Signal(str)
    create_room = Signal()
    quick_match = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rooms_data: List[Dict] = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 头部
        header = QHBoxLayout()
        
        title = QLabel("房间大厅")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {t.text_display};")
        header.addWidget(title)
        
        header.addStretch()
        
        # 快速匹配按钮
        quick_btn = QPushButton("⚡ 快速匹配")
        quick_btn.setFixedHeight(36)
        quick_btn.setCursor(Qt.PointingHandCursor)
        quick_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.warning};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #D97706;
            }}
        """)
        quick_btn.clicked.connect(self.quick_match.emit)
        header.addWidget(quick_btn)
        
        # 创建房间按钮
        create_btn = QPushButton("+ 创建房间")
        create_btn.setFixedHeight(36)
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.primary};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {t.primary_hover};
            }}
        """)
        create_btn.clicked.connect(self.create_room.emit)
        header.addWidget(create_btn)
        
        layout.addLayout(header)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        self.container = QWidget()
        self.rooms_layout = QVBoxLayout(self.container)
        self.rooms_layout.setContentsMargins(0, 0, 8, 0)
        self.rooms_layout.setSpacing(12)
        self.rooms_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll, 1)

    def set_rooms(self, rooms: List[Dict[str, Any]]):
        self.rooms_data = rooms
        self._refresh_list()

    def _refresh_list(self):
        # 清空
        while self.rooms_layout.count() > 1:
            item = self.rooms_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.rooms_data:
            empty = QLabel("暂无房间\n快来创建吧！")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {t.text_caption}; padding: 40px; font-size: 14px;")
            self.rooms_layout.insertWidget(0, empty)
        else:
            for i, room in enumerate(self.rooms_data):
                card = RoomCard(room)
                card.join_clicked.connect(self.join_room.emit)
                self.rooms_layout.insertWidget(i, card)
                
                # 入场动画
                AnimationUtils.slide_in_up(card, 300, 20 + i*30)
