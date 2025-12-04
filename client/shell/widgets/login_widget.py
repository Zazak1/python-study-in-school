"""
登录界面组件 - 2.0 设计升级
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
        
        # 入场动画
        AnimationUtils.slide_in_up(self.card, 600, 30)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # 背景：可以是图片或渐变
        # 这里简单用 theme 背景，实际可用 paintEvent 绘制图案
        
        # 登录卡片
        self.card = QFrame()
        self.card.setObjectName("loginCard")
        self.card.setFixedSize(420, 580)
        # QSS 已定义样式，这里补充阴影
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 20)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(48, 60, 48, 48)
        card_layout.setSpacing(24)
        
        # Logo / 标题
        title = QLabel("Aether Party")
        title.setAlignment(Qt.AlignCenter)
        title.setProperty("class", "display")
        card_layout.addWidget(title)
        
        subtitle = QLabel("跨平台好友对战大厅")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setProperty("class", "caption")
        subtitle.setStyleSheet("font-size: 14px; letter-spacing: 2px;")
        card_layout.addWidget(subtitle)
        
        card_layout.addSpacing(20)
        
        # 输入框
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名 / 邮箱")
        self.username_input.setMinimumHeight(48)
        card_layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(48)
        self.password_input.returnPressed.connect(self._on_login)
        card_layout.addWidget(self.password_input)
        
        # 选项
        opts_layout = QHBoxLayout()
        self.remember_check = QCheckBox("记住我")
        
        forgot_btn = QPushButton("忘记密码?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setProperty("class", "ghost")
        forgot_btn.setStyleSheet(f"color: {t.primary}; font-size: 13px; padding: 0;")
        
        opts_layout.addWidget(self.remember_check)
        opts_layout.addStretch()
        opts_layout.addWidget(forgot_btn)
        card_layout.addLayout(opts_layout)
        
        card_layout.addSpacing(10)
        
        # 按钮
        self.login_btn = QPushButton("进入游戏")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setMinimumHeight(52)
        self.login_btn.setProperty("class", "primary")
        self.login_btn.setStyleSheet("font-size: 16px; border-radius: 12px;")
        self.login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_btn)
        
        # 分割线
        sep_layout = QHBoxLayout()
        line1 = QFrame(); line1.setProperty("class", "divider"); line1.setFrameShape(QFrame.HLine)
        line2 = QFrame(); line2.setProperty("class", "divider"); line2.setFrameShape(QFrame.HLine)
        or_lbl = QLabel("或是"); or_lbl.setProperty("class", "caption"); or_lbl.setStyleSheet("padding: 0 8px;")
        
        sep_layout.addWidget(line1, 1)
        sep_layout.addWidget(or_lbl)
        sep_layout.addWidget(line2, 1)
        card_layout.addLayout(sep_layout)
        
        # 快速登录
        quick_layout = QHBoxLayout()
        for name, color in [("游客", "#6366F1"), ("QQ", "#0EA5E9"), ("微信", "#10B981")]:
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            # 自定义边框按钮
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; color: #475569;
                }}
                QPushButton:hover {{
                    border-color: {color}; color: {color}; background: #F8FAFC;
                }}
            """)
            quick_layout.addWidget(btn)
        card_layout.addLayout(quick_layout)
        
        card_layout.addStretch()
        
        # 注册
        reg_layout = QHBoxLayout()
        reg_layout.setAlignment(Qt.AlignCenter)
        reg_hint = QLabel("还没有账号?"); reg_hint.setProperty("class", "caption")
        
        reg_btn = QPushButton("立即注册")
        reg_btn.setCursor(Qt.PointingHandCursor)
        reg_btn.setProperty("class", "ghost")
        reg_btn.setStyleSheet(f"color: {t.primary}; font-weight: 600;")
        reg_btn.clicked.connect(self.register_requested.emit)
        
        reg_layout.addWidget(reg_hint)
        reg_layout.addWidget(reg_btn)
        card_layout.addLayout(reg_layout)
        
        layout.addWidget(self.card)
        
    def _on_login(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text()
        if user and pwd:
            self.login_requested.emit(user, pwd, self.remember_check.isChecked())
        else:
            self._shake_input()
            
    def _shake_input(self):
        # 简单的抖动反馈：变红 + 定时恢复
        err_style = f"border: 1px solid {t.error}; background: #FEF2F2;"
        if not self.username_input.text(): self.username_input.setStyleSheet(err_style)
        if not self.password_input.text(): self.password_input.setStyleSheet(err_style)
        
        QTimer.singleShot(1000, lambda: self.username_input.setStyleSheet(""))
        QTimer.singleShot(1000, lambda: self.password_input.setStyleSheet(""))

    def set_loading(self, loading):
        self.login_btn.setEnabled(not loading)
        self.login_btn.setText("登录中..." if loading else "进入游戏")
