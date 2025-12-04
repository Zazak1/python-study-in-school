"""
游戏卡片组件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap


class GameCard(QWidget):
    """游戏选择卡片"""
    
    clicked = Signal(str)  # game_id
    
    # 游戏信息配置
    GAMES = {
        'gomoku': {
            'name': '五子棋',
            'icon': '⚫',
            'desc': '经典对弈，策略博弈',
            'players': '2人',
            'color': '#10B981',
            'gradient': ('rgba(16, 185, 129, 0.2)', 'rgba(16, 185, 129, 0.05)')
        },
        'shooter2d': {
            'name': '2D 射击',
            'icon': '🔫',
            'desc': '紧张刺激，快节奏对战',
            'players': '2-8人',
            'color': '#EF4444',
            'gradient': ('rgba(239, 68, 68, 0.2)', 'rgba(239, 68, 68, 0.05)')
        },
        'werewolf': {
            'name': '狼人杀',
            'icon': '🐺',
            'desc': '语音推理，烧脑社交',
            'players': '6-12人',
            'color': '#8B5CF6',
            'gradient': ('rgba(139, 92, 246, 0.2)', 'rgba(139, 92, 246, 0.05)')
        },
        'monopoly': {
            'name': '大富翁',
            'icon': '🎲',
            'desc': '商业帝国，策略经营',
            'players': '2-4人',
            'color': '#F59E0B',
            'gradient': ('rgba(245, 158, 11, 0.2)', 'rgba(245, 158, 11, 0.05)')
        },
        'racing': {
            'name': '赛车竞速',
            'icon': '🏎️',
            'desc': '速度激情，极限漂移',
            'players': '2-6人',
            'color': '#00D4FF',
            'gradient': ('rgba(0, 212, 255, 0.2)', 'rgba(0, 212, 255, 0.05)')
        }
    }
    
    def __init__(self, game_id: str, parent=None):
        super().__init__(parent)
        self.game_id = game_id
        self.game_info = self.GAMES.get(game_id, {})
        self.setup_ui()
    
    def setup_ui(self):
        """设置 UI"""
        info = self.game_info
        color = info.get('color', '#00D4FF')
        grad1, grad2 = info.get('gradient', ('rgba(0,0,0,0.2)', 'rgba(0,0,0,0.05)'))
        
        self.setMinimumSize(180, 200)
        self.setMaximumSize(220, 240)
        self.setCursor(Qt.PointingHandCursor)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 卡片容器
        self.card = QFrame()
        self.card.setObjectName("gameCard")
        self.card.setStyleSheet(f"""
            #gameCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {grad1}, stop:1 {grad2});
                border: 2px solid #2d3748;
                border-radius: 16px;
            }}
            #gameCard:hover {{
                border-color: {color};
            }}
        """)
        
        # 添加发光效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(color))
        shadow.setColor(QColor(0, 0, 0, 80))
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 25, 20, 20)
        card_layout.setSpacing(12)
        
        # 游戏图标
        icon_label = QLabel(info.get('icon', '🎮'))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 48px;
            background: transparent;
        """)
        card_layout.addWidget(icon_label)
        
        # 游戏名称
        name_label = QLabel(info.get('name', '未知游戏'))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {color};
            background: transparent;
        """)
        card_layout.addWidget(name_label)
        
        # 游戏描述
        desc_label = QLabel(info.get('desc', ''))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #94A3B8;
            background: transparent;
        """)
        card_layout.addWidget(desc_label)
        
        # 玩家数
        players_label = QLabel(f"👥 {info.get('players', '?')}")
        players_label.setAlignment(Qt.AlignCenter)
        players_label.setStyleSheet("""
            font-size: 11px;
            color: #64748B;
            background: transparent;
        """)
        card_layout.addWidget(players_label)
        
        card_layout.addStretch()
        
        layout.addWidget(self.card)
    
    def mousePressEvent(self, event):
        """鼠标点击"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.game_id)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入"""
        color = self.game_info.get('color', '#00D4FF')
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(color))
        self.card.setGraphicsEffect(shadow)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.card.setGraphicsEffect(shadow)
        super().leaveEvent(event)

