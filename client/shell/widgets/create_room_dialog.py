"""
创建房间对话框
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QFrame, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ..styles.theme import CURRENT_THEME as t


class GameTypeButton(QPushButton):
    """游戏类型选择按钮"""
    
    def __init__(self, game_id: str, name: str, icon: str, color: str, parent=None):
        super().__init__(parent)
        self.game_id = game_id
        self.color = color
        
        self.setText(f"{icon}\n{name}")
        self.setFixedSize(80, 80)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.bg_card};
                border: 2px solid {t.border_light};
                border-radius: 12px;
                font-size: 12px;
                color: {t.text_body};
            }}
            QPushButton:hover {{
                border-color: {color};
            }}
            QPushButton:checked {{
                background-color: {color}10;
                border-color: {color};
                color: {color};
            }}
        """)


class CreateRoomDialog(QDialog):
    """创建房间对话框"""
    
    room_created = Signal(dict)  # 房间配置
    
    GAMES = {
        'gomoku': {'name': '五子棋', 'icon': '⚫', 'color': '#10B981', 'max': 2},
        'shooter2d': {'name': '2D射击', 'icon': '🔫', 'color': '#EF4444', 'max': 8},
        'werewolf': {'name': '狼人杀', 'icon': '🐺', 'color': '#8B5CF6', 'max': 12},
        'monopoly': {'name': '大富翁', 'icon': '🎲', 'color': '#F59E0B', 'max': 4},
        'racing': {'name': '赛车', 'icon': '🏎️', 'color': '#06B6D4', 'max': 6},
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_game = 'gomoku'
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("创建房间")
        self.setFixedSize(480, 520)
        self.setStyleSheet(f"background-color: {t.bg_card};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 24)
        layout.setSpacing(24)
        
        # 标题
        title = QLabel("创建新房间")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {t.text_display};
        """)
        layout.addWidget(title)
        
        # 游戏类型选择
        game_label = QLabel("选择游戏")
        game_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {t.text_body};")
        layout.addWidget(game_label)
        
        game_layout = QHBoxLayout()
        game_layout.setSpacing(12)
        
        self.game_buttons = QButtonGroup(self)
        
        for game_id, info in self.GAMES.items():
            btn = GameTypeButton(
                game_id, info['name'], info['icon'], info['color']
            )
            if game_id == 'gomoku':
                btn.setChecked(True)
            
            btn.clicked.connect(lambda checked, gid=game_id: self._on_game_selected(gid))
            self.game_buttons.addButton(btn)
            game_layout.addWidget(btn)
        
        game_layout.addStretch()
        layout.addLayout(game_layout)
        
        # 房间名称
        name_label = QLabel("房间名称")
        name_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {t.text_body};")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入房间名称...")
        self.name_input.setFixedHeight(44)
        layout.addWidget(self.name_input)
        
        # 人数设置
        players_layout = QHBoxLayout()
        
        players_label = QLabel("最大人数")
        players_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {t.text_body};")
        players_layout.addWidget(players_label)
        
        players_layout.addStretch()
        
        self.players_spin = QSpinBox()
        self.players_spin.setRange(2, 12)
        self.players_spin.setValue(2)
        self.players_spin.setFixedSize(80, 36)
        self.players_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {t.bg_base};
                border: 1px solid {t.border_normal};
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 14px;
            }}
            QSpinBox:focus {{
                border-color: {t.primary};
            }}
        """)
        players_layout.addWidget(self.players_spin)
        
        layout.addLayout(players_layout)
        
        # 私密房间
        private_layout = QHBoxLayout()
        
        self.private_check = QCheckBox("私密房间（需要密码加入）")
        self.private_check.setStyleSheet(f"color: {t.text_body}; font-size: 13px;")
        self.private_check.toggled.connect(self._on_private_toggled)
        private_layout.addWidget(self.private_check)
        
        private_layout.addStretch()
        layout.addLayout(private_layout)
        
        # 密码
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("设置房间密码...")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(44)
        self.password_input.setEnabled(False)
        layout.addWidget(self.password_input)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedHeight(44)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.bg_base};
                color: {t.text_body};
                border: 1px solid {t.border_normal};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("创建房间")
        create_btn.setFixedHeight(44)
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t.primary};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {t.primary_hover};
            }}
        """)
        create_btn.clicked.connect(self._on_create)
        btn_layout.addWidget(create_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_game_selected(self, game_id: str):
        """游戏选择"""
        self.selected_game = game_id
        info = self.GAMES[game_id]
        self.players_spin.setMaximum(info['max'])
        self.players_spin.setValue(min(self.players_spin.value(), info['max']))
    
    def _on_private_toggled(self, checked: bool):
        """私密开关"""
        self.password_input.setEnabled(checked)
        if not checked:
            self.password_input.clear()
    
    def _on_create(self):
        """创建房间"""
        name = self.name_input.text().strip()
        if not name:
            name = f"{self.GAMES[self.selected_game]['name']}房间"
        
        config = {
            'game_type': self.selected_game,
            'name': name,
            'max_players': self.players_spin.value(),
            'is_private': self.private_check.isChecked(),
            'password': self.password_input.text() if self.private_check.isChecked() else ''
        }
        
        self.room_created.emit(config)
        self.accept()
    
    def get_room_config(self) -> dict:
        """获取房间配置"""
        return {
            'game_type': self.selected_game,
            'name': self.name_input.text().strip() or f"{self.GAMES[self.selected_game]['name']}房间",
            'max_players': self.players_spin.value(),
            'is_private': self.private_check.isChecked(),
            'password': self.password_input.text() if self.private_check.isChecked() else ''
        }

