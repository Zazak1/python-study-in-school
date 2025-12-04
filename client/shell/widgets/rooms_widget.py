"""
房间列表组件 - 现代化浅色风格
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
        
        # 游戏配置
        configs = {
            'gomoku':    {'color': '#10B981', 'name': '五子棋', 'icon': '⚫'},
            'shooter2d': {'color': '#EF4444', 'name': '2D射击', 'icon': '🔫'},
            'werewolf':  {'color': '#8B5CF6', 'name': '狼人杀', 'icon': '🐺'},
            'monopoly':  {'color': '#F59E0B', 'name': '大富翁', 'icon': '🎲'},
            'racing':    {'color': '#06B6D4', 'name': '赛车',   'icon': '🏎️'}
        }
        config = configs.get(game_type, {'color': '#6B7280', 'name': '未知', 'icon': '🎮'})
        color = config['color']
        
        self.setFixedHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        
        # 主框架
        self.frame = QFrame()
        self.frame.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {color};
                background-color: #F9FAFB;
            }}
        """)
        
        frame_layout = QHBoxLayout(self.frame)
        frame_layout.setContentsMargins(16, 10, 16, 10)
        frame_layout.setSpacing(16)
        
        # 游戏图标
        icon_label = QLabel(config['icon'])
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        # 浅色背景圆
        c = QColor(color)
        rgba = f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.1)"
        icon_label.setStyleSheet(f"""
            background-color: {rgba};
            border-radius: 10px;
            font-size: 24px;
            color: {color};
        """)
        frame_layout.addWidget(icon_label)
        
        # 房间信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignVCenter)
        
        # 房间名
        room_name = QLabel(room.get('name', f'房间 #{room.get("room_id", "?")}'))
        room_name.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #111827;
        """)
        info_layout.addWidget(room_name)
        
        # 房间详情
        details_layout = QHBoxLayout()
        details_layout.setSpacing(12)
        
        # 游戏类型标签
        game_label = QLabel(config['name'])
        game_label.setStyleSheet(f"font-size: 12px; color: {color}; font-weight: 500;")
        details_layout.addWidget(game_label)
        
        # 人数
        current = room.get('current_players', 0)
        max_p = room.get('max_players', 8)
        players_label = QLabel(f"👥 {current}/{max_p}")
        players_label.setStyleSheet("font-size: 12px; color: #6B7280;")
        details_layout.addWidget(players_label)
        
        # 房主
        host = room.get('host_name', '未知')
        host_label = QLabel(f"👑 {host}")
        host_label.setStyleSheet("font-size: 12px; color: #9CA3AF;")
        details_layout.addWidget(host_label)
        
        details_layout.addStretch()
        info_layout.addLayout(details_layout)
        
        frame_layout.addLayout(info_layout, 1)
        
        # 状态 & 加入按钮
        is_playing = room.get('is_playing', False)
        is_full = current >= max_p
        
        if is_playing:
            status = QLabel("游戏中")
            status.setStyleSheet("""
                font-size: 12px;
                color: #F59E0B;
                background-color: #FFFBEB;
                padding: 4px 10px;
                border-radius: 6px;
                font-weight: 500;
            """)
            frame_layout.addWidget(status)
        elif is_full:
            status = QLabel("已满")
            status.setStyleSheet("""
                font-size: 12px;
                color: #EF4444;
                background-color: #FEF2F2;
                padding: 4px 10px;
                border-radius: 6px;
                font-weight: 500;
            """)
            frame_layout.addWidget(status)
        else:
            join_btn = QPushButton("加入")
            join_btn.setFixedSize(60, 32)
            join_btn.setCursor(Qt.PointingHandCursor)
            # 覆盖默认样式为当前游戏的主题色
            join_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {self._adjust_color(color, 110)};
                }}
            """)
            join_btn.clicked.connect(
                lambda: self.join_clicked.emit(room.get('room_id', ''))
            )
            frame_layout.addWidget(join_btn)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.frame)

    def _adjust_color(self, hex_color, factor):
        """简单调亮颜色"""
        # 这里只返回原色作为占位，实际可用 QColor.lighter()
        return hex_color


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
        
        title = QLabel("房间大厅")
        title.setProperty("class", "heading")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        header.addWidget(title)
        
        header.addStretch()
        
        # 快速匹配
        quick_btn = QPushButton("⚡ 快速匹配")
        quick_btn.setCursor(Qt.PointingHandCursor)
        quick_btn.setProperty("class", "primary")
        quick_btn.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B;
                border: none;
            }
            QPushButton:hover {
                background-color: #D97706;
            }
        """)
        quick_btn.clicked.connect(self.quick_match.emit)
        header.addWidget(quick_btn)
        
        # 创建房间
        create_btn = QPushButton("+ 创建房间")
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.setProperty("class", "primary")
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
            
            # 胶囊样式
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #6B7280;
                    border: 1px solid #E5E7EB;
                    border-radius: 16px;
                    padding: 4px 16px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    border-color: #2563EB;
                    color: #2563EB;
                }
                QPushButton:checked {
                    background-color: #2563EB;
                    color: #FFFFFF;
                    border-color: #2563EB;
                    font-weight: 600;
                }
            """)
            filter_layout.addWidget(btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 房间列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        self.rooms_container = QWidget()
        self.rooms_layout = QVBoxLayout(self.rooms_container)
        self.rooms_layout.setContentsMargins(0, 0, 8, 0)
        self.rooms_layout.setSpacing(12)
        
        # 空状态占位
        self.empty_widget = QWidget()
        # ... (保持原逻辑)
        
        scroll.setWidget(self.rooms_container)
        layout.addWidget(scroll, 1)
        
        # 初始化空列表
        self._refresh_list()
    
    def set_rooms(self, rooms: List[Dict[str, Any]]):
        """设置房间数据"""
        self.rooms_data = rooms
        self._refresh_list()
    
    def _refresh_list(self):
        """刷新房间列表"""
        # 清空
        while self.rooms_layout.count() > 0:
            item = self.rooms_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.rooms_data:
            # 显示空状态
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignCenter)
            empty_layout.setSpacing(16)
            
            empty_icon = QLabel("🏠")
            empty_icon.setStyleSheet("font-size: 48px; background: transparent;")
            empty_icon.setAlignment(Qt.AlignCenter)
            empty_layout.addWidget(empty_icon)
            
            empty_text = QLabel("暂无可用房间\n创建一个房间或快速匹配吧！")
            empty_text.setAlignment(Qt.AlignCenter)
            empty_text.setStyleSheet("color: #9CA3AF; font-size: 14px;")
            empty_layout.addWidget(empty_text)
            
            self.rooms_layout.addWidget(empty_widget)
            self.rooms_layout.addStretch()
        else:
            for room in self.rooms_data:
                card = RoomCard(room)
                card.join_clicked.connect(self.join_room.emit)
                self.rooms_layout.addWidget(card)
            self.rooms_layout.addStretch()
