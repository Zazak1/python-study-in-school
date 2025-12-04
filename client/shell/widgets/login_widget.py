"""
登录界面组件 - 现代化浅色风格
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
    
    def setup_ui(self):
        """设置 UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        # 背景装饰 (可选)
        # ...
        
        # 中心卡片容器
        card = QFrame()
        card.setObjectName("loginCard")
        # QSS 中已定义 #loginCard 样式 (白色背景, 圆角, 边框)
        
        # 添加柔和阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 20)) # 浅色阴影
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 60, 48, 48)
        card_layout.setSpacing(24)
        
        # Logo 区域
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(12)
        
        # 游戏标题
        title = QLabel("Aether Party")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-family: "PingFang SC", sans-serif;
            font-size: 32px;
            font-weight: 800;
            color: #111827;
            letter-spacing: -0.5px;
        """)
        
        subtitle = QLabel("跨平台好友对战大厅")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #6B7280;
            letter-spacing: 1px;
            font-weight: 500;
        """)
        
        logo_layout.addWidget(title)
        logo_layout.addWidget(subtitle)
        card_layout.addLayout(logo_layout)
        
        # 间隔
        card_layout.addSpacing(20)
        
        # 用户名输入
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名 / 邮箱")
        self.username_input.setMinimumHeight(48)
        # 样式由全局 QSS 接管
        card_layout.addWidget(self.username_input)
        
        # 密码输入
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(48)
        card_layout.addWidget(self.password_input)
        
        # 记住我 & 忘记密码
        options_layout = QHBoxLayout()
        
        self.remember_check = QCheckBox("记住我")
        # 样式由全局 QSS 接管
        
        forgot_btn = QPushButton("忘记密码?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setProperty("class", "ghost") # 使用 ghost 类
        forgot_btn.setStyleSheet("""
            QPushButton {
                color: #2563EB;
                font-size: 13px;
                padding: 0;
                text-align: right;
            }
            QPushButton:hover {
                color: #1D4ED8;
                background: none;
                text-decoration: underline;
            }
        """)
        
        options_layout.addWidget(self.remember_check)
        options_layout.addStretch()
        options_layout.addWidget(forgot_btn)
        card_layout.addLayout(options_layout)
        
        # 间隔
        card_layout.addSpacing(8)
        
        # 登录按钮
        self.login_btn = QPushButton("进入游戏")
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setProperty("class", "primary") # 使用 primary 类
        self.login_btn.clicked.connect(self._on_login)
        card_layout.addWidget(self.login_btn)
        
        # 分割线
        separator_layout = QHBoxLayout()
        separator_layout.setSpacing(16)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("background: #E5E7EB; max-height: 1px; border: none;")
        
        or_label = QLabel("或是")
        or_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background: #E5E7EB; max-height: 1px; border: none;")
        
        separator_layout.addWidget(line1, 1)
        separator_layout.addWidget(or_label)
        separator_layout.addWidget(line2, 1)
        card_layout.addLayout(separator_layout)
        
        # 快速登录按钮组
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(12)
        
        guest_btn = self._create_quick_btn("游客", "#6366F1")
        qq_btn = self._create_quick_btn("QQ", "#0EA5E9")
        wechat_btn = self._create_quick_btn("微信", "#10B981")
        
        quick_layout.addWidget(guest_btn)
        quick_layout.addWidget(qq_btn)
        quick_layout.addWidget(wechat_btn)
        card_layout.addLayout(quick_layout)
        
        # 注册提示
        card_layout.addSpacing(16)
        
        register_layout = QHBoxLayout()
        register_layout.setAlignment(Qt.AlignCenter)
        
        hint = QLabel("还没有账号?")
        hint.setStyleSheet("color: #6B7280; font-size: 13px;")
        
        register_btn = QPushButton("立即注册")
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.setProperty("class", "ghost")
        register_btn.setStyleSheet("""
            QPushButton {
                color: #2563EB;
                font-weight: 600;
                font-size: 13px;
                padding: 0 4px;
            }
            QPushButton:hover {
                color: #1D4ED8;
                background: none;
            }
        """)
        register_btn.clicked.connect(self.register_requested.emit)
        
        register_layout.addWidget(hint)
        register_layout.addWidget(register_btn)
        card_layout.addLayout(register_layout)
        
        layout.addWidget(card)
        
        # 回车键登录
        self.password_input.returnPressed.connect(self._on_login)
    
    def _create_quick_btn(self, text: str, color: str) -> QPushButton:
        """创建快速登录按钮"""
        btn = QPushButton(text)
        btn.setMinimumHeight(40)
        btn.setCursor(Qt.PointingHandCursor)
        # 覆盖默认样式，使用自定义边框色
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                color: #4B5563;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                border-color: {color};
                color: {color};
                background-color: #F9FAFB;
            }}
        """)
        return btn
    
    def _on_login(self):
        """登录按钮点击"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        remember = self.remember_check.isChecked()
        
        if username and password:
            self.login_requested.emit(username, password, remember)
        else:
            self._shake_animation()
    
    def _shake_animation(self):
        """抖动动画"""
        # 简单的错误提示样式
        error_style = """
            border: 1px solid #EF4444;
            background-color: #FEF2F2;
        """
        if not self.username_input.text().strip():
            self.username_input.setStyleSheet(error_style)
        if not self.password_input.text():
            self.password_input.setStyleSheet(error_style)
            
        # 恢复样式 (简单处理：延时恢复)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, lambda: self.username_input.setStyleSheet(""))
        QTimer.singleShot(1000, lambda: self.password_input.setStyleSheet(""))
    
    def set_loading(self, loading: bool):
        """设置加载状态"""
        self.login_btn.setEnabled(not loading)
        if loading:
            self.login_btn.setText("登录中...")
        else:
            self.login_btn.setText("进入游戏")
