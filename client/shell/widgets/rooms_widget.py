"""
房间列表组件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import List, Dict, Any


class RoomCard(QWidget):
    """房间卡片"""
    
    join_clicked = Signal(str)  # room_id
    
    def __init__(self, room_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.room_data = room_data
        self.setup_ui()
    
    def setup_ui(self):
        """设置 UI"""
        room = self.room_data
        game_type = room.get('game_type', 'unknown')
        
        # 游戏颜色映射
        colors = {
            'gomoku': '#10B981',
            'shooter2d': '#EF4444',
            'werewolf': '#8B5CF6',
            'monopoly': '#F59E0B',
            'racing': '#00D4FF'
        }
        color = colors.get(game_type, '#00D4FF')
        
        # 游戏图标映射
        icons = {
            'gomoku': '⚫',
            'shooter2d': '🔫',
            'werewolf': '🐺',
            'monopoly': '🎲',
            'racing': '🏎️'
        }
        icon = icons.get(game_type, '🎮')
        
        # 游戏名称映射
        names = {
            'gomoku': '五子棋',
            'shooter2d': '2D射击',
            'werewolf': '狼人杀',
            'monopoly': '大富翁',
            'racing': '赛车'
        }
        game_name = names.get(game_type, '未知')
        
        self.setFixedHeight(90)
        self.setCursor(Qt.PointingHandCursor)
        
        # 主框架
        self.frame = QFrame()
        self.frame.setStyleSheet(f"""
            QFrame {{
                background: #161E2E;
                border: 1px solid #2d3748;
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {color};
                background: #1a2332;
            }}
        """)
        
        frame_layout = QHBoxLayout(self.frame)
        frame_layout.setContentsMargins(16, 12, 16, 12)
        frame_layout.setSpacing(16)
        
        # 游戏图标
        icon_label = QLabel(icon)
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2);
            border-radius: 12px;
            font-size: 24px;
        """)
        frame_layout.addWidget(icon_label)
        
        # 房间信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # 房间名
        room_name = QLabel(room.get('name', f'房间 #{room.get("room_id", "?")}'))
        room_name.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #F0F4F8;
            background: transparent;
        """)
        info_layout.addWidget(room_name)
        
        # 房间详情
        details_layout = QHBoxLayout()
        details_layout.setSpacing(12)
        
        # 游戏类型
        game_label = QLabel(f"🎮 {game_name}")
        game_label.setStyleSheet(f"""
            font-size: 12px;
            color: {color};
            background: transparent;
        """)
        details_layout.addWidget(game_label)
        
        # 人数
        current = room.get('current_players', 0)
        max_p = room.get('max_players', 8)
        players_label = QLabel(f"👥 {current}/{max_p}")
        players_label.setStyleSheet("""
            font-size: 12px;
            color: #94A3B8;
            background: transparent;
        """)
        details_layout.addWidget(players_label)
        
        # 房主
        host = room.get('host_name', '未知')
        host_label = QLabel(f"👑 {host}")
        host_label.setStyleSheet("""
            font-size: 12px;
            color: #94A3B8;
            background: transparent;
        """)
        details_layout.addWidget(host_label)
        
        details_layout.addStretch()
        info_layout.addLayout(details_layout)
        
        frame_layout.addLayout(info_layout, 1)
        
        # 状态 & 加入按钮
        status_layout = QVBoxLayout()
        status_layout.setAlignment(Qt.AlignCenter)
        
        # 状态标签
        is_playing = room.get('is_playing', False)
        is_full = current >= max_p
        
        if is_playing:
            status = QLabel("游戏中")
            status.setStyleSheet("""
                font-size: 11px;
                color: #F59E0B;
                background: rgba(245, 158, 11, 0.2);
                padding: 4px 8px;
                border-radius: 4px;
            """)
            status_layout.addWidget(status)
        elif is_full:
            status = QLabel("已满")
            status.setStyleSheet("""
                font-size: 11px;
                color: #EF4444;
                background: rgba(239, 68, 68, 0.2);
                padding: 4px 8px;
                border-radius: 4px;
            """)
            status_layout.addWidget(status)
        else:
            join_btn = QPushButton("加入")
            join_btn.setFixedSize(64, 32)
            join_btn.setCursor(Qt.PointingHandCursor)
            join_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: #0A0E17;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: #5CE1FF;
                }}
            """)
            join_btn.clicked.connect(
                lambda: self.join_clicked.emit(room.get('room_id', ''))
            )
            status_layout.addWidget(join_btn)
        
        frame_layout.addLayout(status_layout)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.frame)


class RoomsWidget(QWidget):
    """房间列表面板"""
    
    join_room = Signal(str)    # room_id
    create_room = Signal()
    quick_match = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rooms_data: List[Dict] = []
        self.setup_ui()
    
    def setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # 标题栏
        header = QHBoxLayout()
        
        title = QLabel("🏠 房间大厅")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #F0F4F8;
            background: transparent;
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # 快速匹配
        quick_btn = QPushButton("⚡ 快速匹配")
        quick_btn.setCursor(Qt.PointingHandCursor)
        quick_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF2E97, stop:1 #FF6AB3);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6AB3, stop:1 #FF8EC4);
            }
        """)
        quick_btn.clicked.connect(self.quick_match.emit)
        header.addWidget(quick_btn)
        
        # 创建房间
        create_btn = QPushButton("+ 创建房间")
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.setStyleSheet("""
            QPushButton {
                background: #00D4FF;
                color: #0A0E17;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #5CE1FF;
            }
        """)
        create_btn.clicked.connect(self.create_room.emit)
        header.addWidget(create_btn)
        
        layout.addLayout(header)
        
        # 筛选栏
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        
        filters = ['全部', '五子棋', '2D射击', '狼人杀', '大富翁', '赛车']
        for i, text in enumerate(filters):
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            if i == 0:
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #94A3B8;
                    border: 1px solid #2d3748;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    border-color: #00D4FF;
                    color: #00D4FF;
                }
                QPushButton:checked {
                    background: #00D4FF;
                    color: #0A0E17;
                    border-color: #00D4FF;
                    font-weight: bold;
                }
            """)
            filter_layout.addWidget(btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 房间列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        self.rooms_container = QWidget()
        self.rooms_layout = QVBoxLayout(self.rooms_container)
        self.rooms_layout.setContentsMargins(0, 0, 8, 0)
        self.rooms_layout.setSpacing(8)
        
        # 空状态
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        empty_icon = QLabel("🏠")
        empty_icon.setStyleSheet("font-size: 48px; background: transparent;")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_icon)
        
        empty_text = QLabel("暂无可用房间\n创建一个房间或快速匹配吧！")
        empty_text.setAlignment(Qt.AlignCenter)
        empty_text.setStyleSheet("""
            color: #64748B;
            font-size: 14px;
            background: transparent;
        """)
        empty_layout.addWidget(empty_text)
        
        self.rooms_layout.addWidget(self.empty_widget)
        self.rooms_layout.addStretch()
        
        scroll.setWidget(self.rooms_container)
        layout.addWidget(scroll, 1)
    
    def set_rooms(self, rooms: List[Dict[str, Any]]):
        """设置房间数据"""
        self.rooms_data = rooms
        self._refresh_list()
    
    def _refresh_list(self):
        """刷新房间列表"""
        # 清空现有项
        while self.rooms_layout.count() > 0:
            item = self.rooms_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.rooms_data:
            # 显示空状态
            self.empty_widget = QWidget()
            empty_layout = QVBoxLayout(self.empty_widget)
            empty_layout.setAlignment(Qt.AlignCenter)
            
            empty_icon = QLabel("🏠")
            empty_icon.setStyleSheet("font-size: 48px; background: transparent;")
            empty_icon.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_icon)
            
            empty_text = QLabel("暂无可用房间\n创建一个房间或快速匹配吧！")
            empty_text.setAlignment(Qt.AlignCenter)
            empty_text.setStyleSheet("""
                color: #64748B;
                font-size: 14px;
                background: transparent;
            """)
            empty_layout.addWidget(empty_text)
            
            self.rooms_layout.addWidget(self.empty_widget)
        else:
            for room in self.rooms_data:
                card = RoomCard(room)
                card.join_clicked.connect(self.join_room.emit)
                self.rooms_layout.addWidget(card)
        
        self.rooms_layout.addStretch()

