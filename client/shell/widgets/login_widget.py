"""
登录界面组件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QCheckBox, QFrame,
    QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor


class LoginWidget(QWidget):
    """登录界面"""
    
    # 信号
    login_requested = Signal(str, str, bool)  # username, password, remember
    register_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        """设置 UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        # 中心卡片容器
        card = QFrame()
        card.setObjectName("loginCard")
        card.setStyleSheet("""
            #loginCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a2332, stop:1 #0f1520);
                border: 1px solid #2d3748;
                border-radius: 20px;
                min-width: 400px;
                max-width: 420px;
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 212, 255, 60))
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 50, 40, 40)
        card_layout.setSpacing(20)
        
        # Logo 区域
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(8)
        
        # 游戏标题
        title = QLabel("⚡ AETHER PARTY")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #00D4FF;
            letter-spacing: 3px;
        """)
        
        subtitle = QLabel("跨平台好友对战大厅")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #64748B;
            letter-spacing: 1px;
        """)
        
        logo_layout.addWidget(title)
        logo_layout.addWidget(subtitle)
        card_layout.addLayout(logo_layout)
        
        # 间隔
        card_layout.addSpacing(30)
        
        # 用户名输入
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("👤  用户名 / 邮箱")
        self.username_input.setMinimumHeight(50)
        self.username_input.setStyleSheet(self._input_style())
        card_layout.addWidget(self.username_input)
        
        # 密码输入
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("🔒  密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(50)
        self.password_input.setStyleSheet(self._input_style())
        card_layout.addWidget(self.password_input)
        
        # 记住我 & 忘记密码
        options_layout = QHBoxLayout()
        
        self.remember_check = QCheckBox("记住我")
        self.remember_check.setStyleSheet("""
            QCheckBox {
                color: #94A3B8;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #4A5568;
                background: #1F2937;
            }
            QCheckBox::indicator:checked {
                background: #00D4FF;
                border-color: #00D4FF;
            }
        """)
        
        forgot_btn = QPushButton("忘记密码?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #00D4FF;
                font-size: 13px;
            }
            QPushButton:hover {
                color: #5CE1FF;
                text-decoration: underline;
            }
        """)
        
        options_layout.addWidget(self.remember_check)
        options_layout.addStretch()
        options_layout.addWidget(forgot_btn)
        card_layout.addLayout(options_layout)
        
        # 间隔
        card_layout.addSpacing(10)
        
        # 登录按钮
        self.login_btn = QPushButton("🚀  进入游戏")
        self.login_btn.setMinimumHeight(55)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00D4FF, stop:1 #0099CC);
                color: #0A0E17;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5CE1FF, stop:1 #00D4FF);
            }
            QPushButton:pressed {
                background: #0099CC;
            }
        """)
        self.login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_btn)
        
        # 分割线
        separator_layout = QHBoxLayout()
        separator_layout.setSpacing(15)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("background: #2d3748; max-height: 1px;")
        
        or_label = QLabel("或")
        or_label.setStyleSheet("color: #64748B; font-size: 12px;")
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background: #2d3748; max-height: 1px;")
        
        separator_layout.addWidget(line1, 1)
        separator_layout.addWidget(or_label)
        separator_layout.addWidget(line2, 1)
        card_layout.addLayout(separator_layout)
        
        # 快速登录按钮组
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(12)
        
        guest_btn = self._create_quick_btn("👻 游客体验", "#6366F1")
        qq_btn = self._create_quick_btn("QQ", "#12B7F5")
        wechat_btn = self._create_quick_btn("微信", "#07C160")
        
        quick_layout.addWidget(guest_btn)
        quick_layout.addWidget(qq_btn)
        quick_layout.addWidget(wechat_btn)
        card_layout.addLayout(quick_layout)
        
        # 注册提示
        card_layout.addSpacing(10)
        
        register_layout = QHBoxLayout()
        register_layout.setAlignment(Qt.AlignCenter)
        
        hint = QLabel("还没有账号?")
        hint.setStyleSheet("color: #64748B; font-size: 13px;")
        
        register_btn = QPushButton("立即注册")
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #FF2E97;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FF6AB3;
            }
        """)
        register_btn.clicked.connect(self.register_requested.emit)
        
        register_layout.addWidget(hint)
        register_layout.addWidget(register_btn)
        card_layout.addLayout(register_layout)
        
        layout.addWidget(card)
        
        # 回车键登录
        self.password_input.returnPressed.connect(self._on_login)
    
    def _input_style(self) -> str:
        """输入框样式"""
        return """
            QLineEdit {
                background: #111827;
                border: 2px solid #2d3748;
                border-radius: 12px;
                padding: 0 20px;
                font-size: 14px;
                color: #F0F4F8;
            }
            QLineEdit:focus {
                border-color: #00D4FF;
                background: #1a2332;
            }
            QLineEdit::placeholder {
                color: #4A5568;
            }
        """
    
    def _create_quick_btn(self, text: str, color: str) -> QPushButton:
        """创建快速登录按钮"""
        btn = QPushButton(text)
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px solid {color};
                border-radius: 10px;
                color: {color};
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {color};
                color: #0A0E17;
            }}
        """)
        return btn
    
    def setup_animations(self):
        """设置动画"""
        # 可以添加入场动画
        pass
    
    def _on_login(self):
        """登录按钮点击"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        remember = self.remember_check.isChecked()
        
        if username and password:
            self.login_requested.emit(username, password, remember)
        else:
            # 简单的抖动效果提示
            self._shake_animation()
    
    def _shake_animation(self):
        """抖动动画"""
        # 高亮显示空的输入框
        if not self.username_input.text().strip():
            self.username_input.setStyleSheet(self._input_style().replace(
                "border: 2px solid #2d3748",
                "border: 2px solid #EF4444"
            ))
        if not self.password_input.text():
            self.password_input.setStyleSheet(self._input_style().replace(
                "border: 2px solid #2d3748", 
                "border: 2px solid #EF4444"
            ))
    
    def set_loading(self, loading: bool):
        """设置加载状态"""
        self.login_btn.setEnabled(not loading)
        if loading:
            self.login_btn.setText("⏳  登录中...")
        else:
            self.login_btn.setText("🚀  进入游戏")

