"""
游戏卡片组件 - 2.0 设计升级（修复布局）
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor

from ..styles.theme import CURRENT_THEME as t


class GameCard(QWidget):
    """高级游戏卡片"""
    
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
        self.theme_color = QColor(self.info.get('color', '#3B82F6'))
        self.default_pos = QPoint(0, 0)  # 记录默认位置
        
        self.setFixedSize(180, 220)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        # 主布局 - 为阴影留出空间
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 卡片主体
        self.card = QFrame()
        self.card.setObjectName("gameCard")
        self.card.setStyleSheet(f"""
            #gameCard {{
                background-color: #FFFFFF;
                border: 1px solid {t.border_light};
                border-radius: 20px;
            }}
        """)
        
        # 阴影
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 6)
        self.shadow.setColor(QColor(0, 0, 0, 15))
        self.card.setGraphicsEffect(self.shadow)
        
        # 内部布局
        inner = QVBoxLayout(self.card)
        inner.setContentsMargins(16, 20, 16, 16)
        inner.setSpacing(10)
        
        # 图标容器 - 固定居中
        icon_widget = QWidget()
        icon_widget.setFixedSize(72, 72)
        
        icon_bg = QFrame(icon_widget)
        icon_bg.setGeometry(0, 0, 72, 72)
        icon_bg.setStyleSheet(f"""
            background-color: {self.info.get('bg', '#F3F4F6')};
            border-radius: 36px;
        """)
        
        icon_label = QLabel(self.info.get('icon', '🎮'), icon_widget)
        icon_label.setGeometry(0, 0, 72, 72)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 36px; background: transparent;")
        
        # 居中图标
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        icon_layout.addWidget(icon_widget)
        icon_layout.addStretch()
        inner.addLayout(icon_layout)
        
        inner.addSpacing(4)
        
        # 游戏名
        name = QLabel(self.info.get('name', '未知'))
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(False)
        name.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {t.text_display};
            background: transparent;
        """)
        inner.addWidget(name)
        
        # 描述
        desc = QLabel(self.info.get('desc', ''))
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setMaximumHeight(36)
        desc.setStyleSheet(f"""
            font-size: 12px;
            color: {t.text_caption};
            background: transparent;
            line-height: 1.4;
        """)
        inner.addWidget(desc)
        
        inner.addSpacing(4)
        
        # 玩家数标签
        players = QLabel(f"👥 {self.info.get('players', '?')}")
        players.setAlignment(Qt.AlignCenter)
        players.setStyleSheet(f"""
            font-size: 11px;
            color: {self.info.get('color')};
            font-weight: 600;
            background-color: {self.info.get('bg')};
            border-radius: 6px;
            padding: 4px 10px;
        """)
        
        player_layout = QHBoxLayout()
        player_layout.addStretch()
        player_layout.addWidget(players)
        player_layout.addStretch()
        inner.addLayout(player_layout)
        
        inner.addStretch()
        layout.addWidget(self.card)

    def setup_animations(self):
        """设置动画"""
        self.anim_float = QPropertyAnimation(self.card, b"geometry")
        self.anim_float.setDuration(200)
        self.anim_float.setEasingCurve(QEasingCurve.OutCubic)
        
    def enterEvent(self, event):
        """悬停：上浮 + 彩色阴影"""
        # 获取当前 geometry
        current = self.card.geometry()
        # 向上浮 4px
        target = current.adjusted(0, -4, 0, -4)
        
        self.anim_float.stop()
        self.anim_float.setStartValue(current)
        self.anim_float.setEndValue(target)
        self.anim_float.start()
        
        # 彩色阴影
        c = self.theme_color
        self.shadow.setColor(QColor(c.red(), c.green(), c.blue(), 80))
        self.shadow.setBlurRadius(30)
        self.shadow.setOffset(0, 10)
        
        # 边框变色
        self.card.setStyleSheet(f"""
            #gameCard {{
                background-color: #FFFFFF;
                border: 1px solid {self.info.get('color')};
                border-radius: 20px;
            }}
        """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """离开：恢复"""
        current = self.card.geometry()
        target = current.adjusted(0, 4, 0, 4)
        
        self.anim_float.stop()
        self.anim_float.setStartValue(current)
        self.anim_float.setEndValue(target)
        self.anim_float.start()
        
        # 恢复阴影
        self.shadow.setColor(QColor(0, 0, 0, 15))
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 6)
        
        # 恢复边框
        self.card.setStyleSheet(f"""
            #gameCard {{
                background-color: #FFFFFF;
                border: 1px solid {t.border_light};
                border-radius: 20px;
            }}
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.game_id)
        super().mousePressEvent(event)
