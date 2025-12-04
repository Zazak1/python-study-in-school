"""
游戏卡片组件 - 2.0 设计升级
支持：图标悬停上浮、彩色弥散阴影、背景视差
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QCursor

from ..styles.theme import CURRENT_THEME as t


class GameCard(QWidget):
    """高级游戏卡片"""
    
    clicked = Signal(str)
    
    # 游戏配置：配色更高级
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
        
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        self.setFixedSize(180, 220)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10) # 给阴影留空间
        
        # 卡片主体
        self.card = QFrame()
        self.card.setObjectName("gameCard") # 使用 QSS 基础样式
        self.card.setStyleSheet(f"""
            #gameCard {{
                background-color: #FFFFFF;
                border: 1px solid {t.border_light};
                border-radius: 24px;
            }}
        """)
        
        # 弥散阴影 (默认淡)
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 8)
        self.shadow.setColor(QColor(0, 0, 0, 15))
        self.card.setGraphicsEffect(self.shadow)
        
        # 内部布局
        inner_layout = QVBoxLayout(self.card)
        inner_layout.setContentsMargins(16, 24, 16, 20)
        inner_layout.setSpacing(12)
        
        # 1. 图标容器 (带背景色)
        self.icon_container = QLabel()
        self.icon_container.setFixedSize(72, 72)
        self.icon_container.setAlignment(Qt.AlignCenter)
        
        # 计算背景色 RGBA
        bg_color = self.info.get('bg', '#F3F4F6')
        self.icon_container.setStyleSheet(f"""
            background-color: {bg_color};
            border-radius: 36px;
        """)
        
        # 图标
        self.icon_label = QLabel(self.info.get('icon', '🎮'))
        self.icon_label.setParent(self.icon_container)
        self.icon_label.setStyleSheet("font-size: 36px; background: transparent;")
        self.icon_label.move(18, 14) # 微调居中
        
        # 居中放置图标
        h_box = QHBoxLayout()
        h_box.addStretch()
        h_box.addWidget(self.icon_container)
        h_box.addStretch()
        inner_layout.addLayout(h_box)
        
        # 2. 文本信息
        self.name_label = QLabel(self.info.get('name', '未知'))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {t.text_display};
        """)
        inner_layout.addWidget(self.name_label)
        
        self.desc_label = QLabel(self.info.get('desc', ''))
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(f"""
            font-size: 12px;
            color: {t.text_caption};
            line-height: 1.4;
        """)
        inner_layout.addWidget(self.desc_label)
        
        # 3. 底部标签 (人数)
        self.players_label = QLabel(f"👥 {self.info.get('players', '?')}")
        self.players_label.setAlignment(Qt.AlignCenter)
        self.players_label.setStyleSheet(f"""
            font-size: 11px;
            color: {self.info.get('color')};
            font-weight: 600;
            background-color: {bg_color};
            border-radius: 6px;
            padding: 4px 8px;
        """)
        
        h_box2 = QHBoxLayout()
        h_box2.addStretch()
        h_box2.addWidget(self.players_label)
        h_box2.addStretch()
        inner_layout.addLayout(h_box2)
        
        inner_layout.addStretch()
        layout.addWidget(self.card)

    def setup_animations(self):
        """设置动效"""
        # 浮起动画
        self.anim_float = QPropertyAnimation(self.card, b"pos")
        self.anim_float.setDuration(200)
        self.anim_float.setEasingCurve(QEasingCurve.OutQuad)
        
        # 图标缩放动画 (这里用简单的位移代替，因为 QLabel 缩放复杂)
        self.anim_icon = QPropertyAnimation(self.icon_container, b"pos")
        
    def enterEvent(self, event):
        """悬停: 上浮 + 阴影加深 + 边框变色"""
        # 1. 上浮
        orig_pos = self.card.pos()
        self.anim_float.setStartValue(orig_pos)
        self.anim_float.setEndValue(QPoint(orig_pos.x(), 6)) # 假设 margin 10, 上浮 4px
        self.anim_float.start()
        
        # 2. 阴影: 变成彩色弥散
        c = self.theme_color
        self.shadow.setColor(QColor(c.red(), c.green(), c.blue(), 80)) # 彩色阴影
        self.shadow.setBlurRadius(30)
        self.shadow.setOffset(0, 12)
        
        # 3. 边框
        self.card.setStyleSheet(f"""
            #gameCard {{
                background-color: #FFFFFF;
                border: 1px solid {self.info.get('color')};
                border-radius: 24px;
            }}
        """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """离开: 恢复"""
        # 1. 下落
        self.anim_float.setEndValue(QPoint(10, 10)) # 回到 margin 位置
        self.anim_float.start()
        
        # 2. 阴影恢复
        self.shadow.setColor(QColor(0, 0, 0, 15))
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 8)
        
        # 3. 边框恢复
        self.card.setStyleSheet(f"""
            #gameCard {{
                background-color: #FFFFFF;
                border: 1px solid {t.border_light};
                border-radius: 24px;
            }}
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.game_id)
