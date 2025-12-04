"""
游戏卡片组件 - 简化稳定版
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ..styles.theme import CURRENT_THEME as t


class GameCard(QWidget):
    """游戏卡片"""
    
    clicked = Signal(str)
    
    GAMES = {
        'gomoku': {
            'name': '五子棋', 'icon': '⚫', 
            'desc': '黑白对弈，智者争锋', 
            'players': '2人',
            'color': '#10B981', 'bg': '#ECFDF5'
        },
        'shooter2d': {
            'name': '2D 射击', 'icon': '🔫', 
            'desc': '火力全开，生存竞技', 
            'players': '2-8人',
            'color': '#EF4444', 'bg': '#FEF2F2'
        },
        'werewolf': {
            'name': '狼人杀', 'icon': '🐺', 
            'desc': '谎言与推理的博弈', 
            'players': '6-12人',
            'color': '#8B5CF6', 'bg': '#F5F3FF'
        },
        'monopoly': {
            'name': '大富翁', 'icon': '🎲', 
            'desc': '运筹帷幄，商业大亨', 
            'players': '2-4人',
            'color': '#F59E0B', 'bg': '#FFFBEB'
        },
        'racing': {
            'name': '赛车竞速', 'icon': '🏎️', 
            'desc': '极速漂移，超越极限', 
            'players': '2-6人',
            'color': '#06B6D4', 'bg': '#ECFEFF'
        }
    }
    
    def __init__(self, game_id: str, parent=None):
        super().__init__(parent)
        self.game_id = game_id
        self.info = self.GAMES.get(game_id, {})
        
        self.setFixedSize(160, 210)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 8)
        
        # 卡片主体
        self.card = QFrame()
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {self.info.get('color', t.primary)};
            }}
        """)
        
        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 12))
        self.card.setGraphicsEffect(shadow)
        
        # 内部布局
        inner = QVBoxLayout(self.card)
        inner.setContentsMargins(14, 16, 14, 14)
        inner.setSpacing(8)
        
        # 图标容器 - 固定居中
        icon_container = QWidget()
        icon_container.setFixedSize(64, 64)
        
        icon_bg = QFrame(icon_container)
        icon_bg.setGeometry(0, 0, 64, 64)
        icon_bg.setStyleSheet(f"""
            background-color: {self.info.get('bg', '#F3F4F6')};
            border-radius: 32px;
        """)
        
        icon_label = QLabel(self.info.get('icon', '🎮'), icon_container)
        icon_label.setGeometry(0, 0, 64, 64)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        
        # 居中图标
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(icon_container)
        icon_layout.addStretch()
        inner.addLayout(icon_layout)
        
        # 游戏名
        name = QLabel(self.info.get('name', '未知'))
        name.setAlignment(Qt.AlignCenter)
        name.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 700;
            color: {t.text_display};
        """)
        inner.addWidget(name)
        
        # 描述
        desc = QLabel(self.info.get('desc', ''))
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setFixedHeight(32)
        desc.setStyleSheet(f"""
            font-size: 11px;
            color: {t.text_caption};
        """)
        inner.addWidget(desc)
        
        # 玩家数标签
        players = QLabel(f"👥 {self.info.get('players', '?')}")
        players.setAlignment(Qt.AlignCenter)
        players.setFixedHeight(22)
        players.setStyleSheet(f"""
            font-size: 11px;
            color: {self.info.get('color')};
            font-weight: 600;
            background-color: {self.info.get('bg')};
            border-radius: 6px;
            padding: 2px 8px;
        """)
        
        player_layout = QHBoxLayout()
        player_layout.addStretch()
        player_layout.addWidget(players)
        player_layout.addStretch()
        inner.addLayout(player_layout)
        
        inner.addStretch()
        layout.addWidget(self.card)

    def enterEvent(self, event):
        """悬停效果"""
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 2px solid {self.info.get('color', t.primary)};
                border-radius: 16px;
            }}
        """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """离开恢复"""
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.game_id)
        super().mousePressEvent(event)
