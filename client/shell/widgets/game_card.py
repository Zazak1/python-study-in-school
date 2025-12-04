"""
游戏卡片组件 - 现代化浅色风格
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
            'color': '#10B981', # Green
            'bg': '#ECFDF5'     # Light Green
        },
        'shooter2d': {
            'name': '2D 射击',
            'icon': '🔫',
            'desc': '紧张刺激，快节奏对战',
            'players': '2-8人',
            'color': '#EF4444', # Red
            'bg': '#FEF2F2'     # Light Red
        },
        'werewolf': {
            'name': '狼人杀',
            'icon': '🐺',
            'desc': '语音推理，烧脑社交',
            'players': '6-12人',
            'color': '#8B5CF6', # Purple
            'bg': '#F5F3FF'     # Light Purple
        },
        'monopoly': {
            'name': '大富翁',
            'icon': '🎲',
            'desc': '商业帝国，策略经营',
            'players': '2-4人',
            'color': '#F59E0B', # Amber
            'bg': '#FFFBEB'     # Light Amber
        },
        'racing': {
            'name': '赛车竞速',
            'icon': '🏎️',
            'desc': '速度激情，极限漂移',
            'players': '2-6人',
            'color': '#06B6D4', # Cyan
            'bg': '#ECFEFF'     # Light Cyan
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
        theme_color = info.get('color', '#2563EB')
        bg_color = info.get('bg', '#F3F4F6')
        
        self.setMinimumSize(160, 180)
        self.setMaximumSize(200, 220)
        self.setCursor(Qt.PointingHandCursor)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 卡片容器
        self.card = QFrame()
        self.card.setObjectName("gameCard")
        self.card.setStyleSheet(f"""
            #gameCard {{
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
            }}
            #gameCard:hover {{
                border-color: {theme_color};
                background-color: {bg_color};
            }}
        """)
        
        # 默认阴影
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 15)) # 浅色阴影
        self.card.setGraphicsEffect(self.shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 20, 16, 16)
        card_layout.setSpacing(8)
        
        # 游戏图标背景圆
        icon_container = QLabel()
        icon_container.setFixedSize(64, 64)
        icon_container.setAlignment(Qt.AlignCenter)
        # 使用半透明背景
        rgba_color = self._hex_to_rgba(theme_color, 0.1)
        icon_container.setStyleSheet(f"""
            background-color: {rgba_color};
            border-radius: 32px;
            margin-bottom: 8px;
        """)
        
        # 图标文字
        icon_label = QLabel(info.get('icon', '🎮'))
        icon_label.setParent(icon_container)
        icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        icon_label.move(16, 12) # 简单居中微调
        
        # 添加到布局居中
        h_box = QHBoxLayout()
        h_box.addStretch()
        h_box.addWidget(icon_container)
        h_box.addStretch()
        card_layout.addLayout(h_box)
        
        # 游戏名称
        name_label = QLabel(info.get('name', '未知游戏'))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: #111827;
            background: transparent;
        """)
        card_layout.addWidget(name_label)
        
        # 游戏描述
        desc_label = QLabel(info.get('desc', ''))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: #6B7280;
            background: transparent;
        """)
        card_layout.addWidget(desc_label)
        
        # 玩家数标签
        players_label = QLabel(f"👥 {info.get('players', '?')}")
        players_label.setAlignment(Qt.AlignCenter)
        players_label.setStyleSheet(f"""
            font-size: 11px;
            color: {theme_color};
            font-weight: 600;
            background: transparent;
            padding-top: 4px;
        """)
        card_layout.addWidget(players_label)
        
        card_layout.addStretch()
        
        layout.addWidget(self.card)
    
    def _hex_to_rgba(self, hex_color, alpha):
        """辅助函数：Hex转RGBA"""
        c = QColor(hex_color)
        return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha})"
    
    def mousePressEvent(self, event):
        """鼠标点击"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.game_id)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入"""
        # 加深阴影
        self.shadow.setBlurRadius(30)
        self.shadow.setYOffset(8)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        # 微微上浮效果通过 margin 实现稍微复杂，这里只做阴影变化
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开"""
        self.shadow.setBlurRadius(20)
        self.shadow.setYOffset(4)
        self.shadow.setColor(QColor(0, 0, 0, 15))
        super().leaveEvent(event)
