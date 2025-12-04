"""
设置页面组件
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSlider, QCheckBox,
    QComboBox, QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from ..styles.theme import CURRENT_THEME as t


class SettingSection(QFrame):
    """设置分组"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 12px;
            }}
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {t.text_display};
        """)
        self.layout.addWidget(title_label)
    
    def add_setting(self, widget: QWidget):
        """添加设置项"""
        self.layout.addWidget(widget)


class SettingRow(QWidget):
    """设置行"""
    
    def __init__(self, label: str, description: str = "", parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(16)
        
        # 左侧文字
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 500;
            color: {t.text_display};
        """)
        text_layout.addWidget(label_widget)
        
        if description:
            desc_widget = QLabel(description)
            desc_widget.setStyleSheet(f"""
                font-size: 12px;
                color: {t.text_caption};
            """)
            text_layout.addWidget(desc_widget)
        
        layout.addLayout(text_layout, 1)
        
        # 右侧控件容器
        self.control_layout = QHBoxLayout()
        self.control_layout.setSpacing(8)
        layout.addLayout(self.control_layout)
    
    def add_control(self, widget: QWidget):
        """添加控件"""
        self.control_layout.addWidget(widget)


class VolumeSlider(QSlider):
    """音量滑块"""
    
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setFixedWidth(150)
        self.setRange(0, 100)
        self.setValue(80)
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {t.bg_base};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {t.primary};
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {t.primary};
                border-radius: 3px;
            }}
        """)


class SettingsWidget(QWidget):
    """设置页面"""
    
    settings_changed = Signal(dict)
    logout_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # 标题
        header = QHBoxLayout()
        
        title = QLabel("设置")
        title.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 800;
            color: {t.text_display};
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(40, 40)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.bg_base};
                border: none;
                border-radius: 20px;
                font-size: 20px;
                color: {t.text_caption};
            }}
            QPushButton:hover {{
                background: {t.bg_hover};
                color: {t.text_display};
            }}
        """)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        
        layout.addLayout(header)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 16, 0)
        content_layout.setSpacing(20)
        
        # ========== 声音设置 ==========
        sound_section = SettingSection("🔊 声音")
        
        # 音效
        sound_row = SettingRow("游戏音效", "游戏内的音效")
        self.sound_check = QCheckBox()
        self.sound_check.setChecked(True)
        sound_row.add_control(self.sound_check)
        self.sound_slider = VolumeSlider()
        sound_row.add_control(self.sound_slider)
        sound_section.add_setting(sound_row)
        
        # 音乐
        music_row = SettingRow("背景音乐", "大厅和游戏内的背景音乐")
        self.music_check = QCheckBox()
        self.music_check.setChecked(True)
        music_row.add_control(self.music_check)
        self.music_slider = VolumeSlider()
        self.music_slider.setValue(50)
        music_row.add_control(self.music_slider)
        sound_section.add_setting(music_row)
        
        content_layout.addWidget(sound_section)
        
        # ========== 显示设置 ==========
        display_section = SettingSection("🖥️ 显示")
        
        # 主题
        theme_row = SettingRow("主题", "界面配色方案")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.setFixedWidth(120)
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                background: {t.bg_base};
                border: 1px solid {t.border_normal};
                border-radius: 6px;
                padding: 6px 12px;
            }}
        """)
        theme_row.add_control(self.theme_combo)
        display_section.add_setting(theme_row)
        
        # FPS
        fps_row = SettingRow("显示帧率", "在游戏中显示 FPS")
        self.fps_check = QCheckBox()
        fps_row.add_control(self.fps_check)
        display_section.add_setting(fps_row)
        
        content_layout.addWidget(display_section)
        
        # ========== 通知设置 ==========
        notif_section = SettingSection("🔔 通知")
        
        notif_row = SettingRow("桌面通知", "接收好友邀请和消息提醒")
        self.notif_check = QCheckBox()
        self.notif_check.setChecked(True)
        notif_row.add_control(self.notif_check)
        notif_section.add_setting(notif_row)
        
        content_layout.addWidget(notif_section)
        
        # ========== 账号设置 ==========
        account_section = SettingSection("👤 账号")
        
        # 退出登录
        logout_row = SettingRow("退出登录", "退出当前账号")
        logout_btn = QPushButton("退出")
        logout_btn.setFixedSize(80, 32)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.error};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #DC2626;
            }}
        """)
        logout_btn.clicked.connect(self.logout_requested.emit)
        logout_row.add_control(logout_btn)
        account_section.add_setting(logout_row)
        
        content_layout.addWidget(account_section)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton("保存设置")
        save_btn.setFixedSize(120, 44)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.primary};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {t.primary_hover};
            }}
        """)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _save_settings(self):
        """保存设置"""
        settings = {
            'sound_enabled': self.sound_check.isChecked(),
            'sound_volume': self.sound_slider.value() / 100,
            'music_enabled': self.music_check.isChecked(),
            'music_volume': self.music_slider.value() / 100,
            'theme': self.theme_combo.currentText(),
            'show_fps': self.fps_check.isChecked(),
            'notifications_enabled': self.notif_check.isChecked(),
        }
        self.settings_changed.emit(settings)
    
    def load_settings(self, settings: dict):
        """加载设置"""
        self.sound_check.setChecked(settings.get('sound_enabled', True))
        self.sound_slider.setValue(int(settings.get('sound_volume', 0.8) * 100))
        self.music_check.setChecked(settings.get('music_enabled', True))
        self.music_slider.setValue(int(settings.get('music_volume', 0.5) * 100))
        self.fps_check.setChecked(settings.get('show_fps', False))
        self.notif_check.setChecked(settings.get('notifications_enabled', True))

