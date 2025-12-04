"""
登录界面组件 - 修复布局和居中
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QCheckBox, QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor

from ..utils.animation import AnimationUtils
from ..styles.theme import CURRENT_THEME as t


class LoginWidget(QWidget):
    """登录界面"""
    
    login_requested = Signal(str, str, bool)
    register_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # 延迟入场动画，确保窗口已显示
        QTimer.singleShot(100, lambda: AnimationUtils.slide_in_up(self.card, 500, 30))
    
    def setup_ui(self):
        # 主布局 - 垂直居中
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        # 登录卡片 - 固定尺寸
        self.card = QFrame()
        self.card.setObjectName("loginCard")
        self.card.setFixedSize(440, 600)
        
        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 20)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.card.setGraphicsEffect(shadow)
        
        # 卡片内容
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(48, 60, 48, 48)
        card_layout.setSpacing(20)
        
        # Logo 区域
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(8)
        
        title = QLabel("Aether Party")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 36px;
            font-weight: 800;
            color: {t.text_display};
            letter-spacing: -1px;
        """)
        logo_layout.addWidget(title)
        
        subtitle = QLabel("跨平台好友对战大厅")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: 14px;
            color: {t.text_caption};
            letter-spacing: 2px;
        """)
        logo_layout.addWidget(subtitle)
        
        card_layout.addLayout(logo_layout)
        card_layout.addSpacing(20)
        
        # 输入框
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名 / 邮箱")
        self.username_input.setFixedHeight(48)
        card_layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(48)
        self.password_input.returnPressed.connect(self._on_login)
        card_layout.addWidget(self.password_input)
        
        # 选项行
        options_layout = QHBoxLayout()
        
        self.remember_check = QCheckBox("记住我")
        self.remember_check.setStyleSheet(f"color: {t.text_caption}; font-size: 13px;")
        options_layout.addWidget(self.remember_check)
        
        options_layout.addStretch()
        
        forgot_btn = QPushButton("忘记密码?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {t.primary};
                font-size: 13px;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {t.primary_hover};
                text-decoration: underline;
            }}
        """)
        options_layout.addWidget(forgot_btn)
        
        card_layout.addLayout(options_layout)
        card_layout.addSpacing(10)
        
        # 登录按钮
        self.login_btn = QPushButton("进入游戏")
        self.login_btn.setFixedHeight(52)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.primary};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {t.primary_hover};
            }}
            QPushButton:pressed {{
                background-color: {t.primary_pressed};
            }}
        """)
        self.login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_btn)
        
        # 分割线
        divider_layout = QHBoxLayout()
        divider_layout.setSpacing(12)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet(f"background-color: {t.border_normal}; max-height: 1px; border: none;")
        
        or_label = QLabel("或是")
        or_label.setStyleSheet(f"color: {t.text_caption}; font-size: 12px;")
        or_label.setAlignment(Qt.AlignCenter)
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet(f"background-color: {t.border_normal}; max-height: 1px; border: none;")
        
        divider_layout.addWidget(line1, 1)
        divider_layout.addWidget(or_label)
        divider_layout.addWidget(line2, 1)
        
        card_layout.addLayout(divider_layout)
        
        # 快速登录
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(12)
        
        for text, color in [("游客", "#6366F1"), ("QQ", "#0EA5E9"), ("微信", "#10B981")]:
            btn = QPushButton(text)
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    border: 1px solid {t.border_normal};
                    border-radius: 8px;
                    color: {t.text_body};
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    border-color: {color};
                    color: {color};
                    background-color: {t.bg_hover};
                }}
            """)
            quick_layout.addWidget(btn)
        
        card_layout.addLayout(quick_layout)
        
        card_layout.addStretch()
        
        # 注册提示
        register_layout = QHBoxLayout()
        register_layout.setAlignment(Qt.AlignCenter)
        
        hint = QLabel("还没有账号?")
        hint.setStyleSheet(f"color: {t.text_caption}; font-size: 13px;")
        register_layout.addWidget(hint)
        
        register_btn = QPushButton("立即注册")
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {t.primary};
                font-size: 13px;
                font-weight: 600;
                padding: 0 4px;
            }}
            QPushButton:hover {{
                color: {t.primary_hover};
            }}
        """)
        register_btn.clicked.connect(self.register_requested.emit)
        register_layout.addWidget(register_btn)
        
        card_layout.addLayout(register_layout)
        
        layout.addWidget(self.card)
    
    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if username and password:
            self.login_requested.emit(username, password, self.remember_check.isChecked())
        else:
            self._shake_input()
    
    def _shake_input(self):
        """错误反馈"""
        error_style = f"border: 2px solid {t.error}; background-color: #FEF2F2;"
        
        if not self.username_input.text().strip():
            self.username_input.setStyleSheet(error_style)
            QTimer.singleShot(1000, lambda: self.username_input.setStyleSheet(""))
        
        if not self.password_input.text():
            self.password_input.setStyleSheet(error_style)
            QTimer.singleShot(1000, lambda: self.password_input.setStyleSheet(""))
    
    def set_loading(self, loading: bool):
        self.login_btn.setEnabled(not loading)
        self.login_btn.setText("登录中..." if loading else "进入游戏")
