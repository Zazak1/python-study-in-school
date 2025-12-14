"""
游戏卡片组件 - 简化稳定版
"""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGraphicsDropShadowEffect,
    QPushButton,
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
            'category': '策略',
            'players': '2人',
            'gradient': ('#10B981', '#0D9488'),
        },
        'shooter2d': {
            'name': '2D 射击', 'icon': '🔫', 
            'desc': '火力全开，生存竞技',
            'category': '动作',
            'players': '2-8人',
            'gradient': ('#F97316', '#DC2626'),
        },
        'werewolf': {
            'name': '狼人杀', 'icon': '🐺', 
            'desc': '谎言与推理的博弈',
            'category': '社交',
            'players': '6-12人',
            'gradient': ('#8B5CF6', '#4F46E5'),
        },
        'monopoly': {
            'name': '大富翁', 'icon': '🎲', 
            'desc': '运筹帷幄，商业大亨',
            'category': '聚会',
            'players': '2-4人',
            'gradient': ('#F59E0B', '#F97316'),
        },
        'racing': {
            'name': '赛车竞速', 'icon': '🏎️', 
            'desc': '极速漂移，超越极限',
            'category': '竞速',
            'players': '2-6人',
            'gradient': ('#06B6D4', '#0284C7'),
        }
    }
    
    def __init__(self, game_id: str, parent=None):
        super().__init__(parent)
        self.game_id = game_id
        self.info = self.GAMES.get(game_id, {})
        
        self.setFixedSize(220, 260)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setup_ui()
        
    def setup_ui(self):
        grad_from, grad_to = self.info.get("gradient", (t.primary, "#7C3AED"))

        # 主布局（外边距用于阴影空间）
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 10)
        
        # 卡片主体
        self.card = QFrame()
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid {t.border_light};
                border-radius: 20px;
            }}
            QFrame:hover {{
                border-color: {t.primary};
            }}
        """)
        
        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 16))
        self.card.setGraphicsEffect(shadow)
        
        # 内部布局
        inner = QVBoxLayout(self.card)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # 顶部渐变区域
        hero = QFrame()
        hero.setFixedHeight(96)
        hero.setStyleSheet(
            f"""
            QFrame {{
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {grad_from}, stop:1 {grad_to});
            }}
            """
        )
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(14, 12, 14, 12)
        hero_layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        icon = QLabel(self.info.get("icon", "🎮"))
        icon.setFixedSize(52, 52)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 28px; background: transparent;")
        top_row.addWidget(icon)

        top_row.addStretch()

        category = QLabel(self.info.get("category", "对战"))
        category.setStyleSheet(
            """
            background-color: rgba(255, 255, 255, 0.20);
            border: 1px solid rgba(255, 255, 255, 0.25);
            color: white;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 800;
            """
        )
        top_row.addWidget(category)
        hero_layout.addLayout(top_row)
        inner.addWidget(hero)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 14, 16, 14)
        body_layout.setSpacing(10)

        # 游戏名 + 玩家数
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        name = QLabel(self.info.get("name", "未知"))
        name.setStyleSheet(f"font-size: 16px; font-weight: 900; color: {t.text_display};")
        row.addWidget(name, 1)

        players = QLabel(f"👥 {self.info.get('players', '?')}")
        players.setStyleSheet(
            f"""
            background-color: {t.bg_hover};
            color: {t.text_caption};
            border: 1px solid {t.border_light};
            padding: 3px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 800;
            """
        )
        row.addWidget(players)
        body_layout.addLayout(row)

        # 描述
        desc = QLabel(self.info.get("desc", ""))
        desc.setWordWrap(True)
        desc.setFixedHeight(36)
        desc.setStyleSheet(f"font-size: 12px; color: {t.text_caption}; font-weight: 600;")
        body_layout.addWidget(desc)

        # CTA
        self.cta = QPushButton("开始游戏")
        self.cta.setCursor(Qt.PointingHandCursor)
        self.cta.setFixedHeight(36)
        self.cta.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {t.bg_hover};
                color: {t.text_display};
                border: 1px solid {t.border_normal};
                border-radius: 14px;
                font-size: 12px;
                font-weight: 900;
            }}
            QPushButton:hover {{
                background-color: {t.primary};
                color: white;
                border-color: {t.primary};
            }}
            """
        )
        self.cta.clicked.connect(lambda: self.clicked.emit(self.game_id))
        body_layout.addWidget(self.cta)

        body_layout.addStretch(1)
        inner.addWidget(body, 1)

        layout.addWidget(self.card)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.game_id)
        super().mousePressEvent(event)
