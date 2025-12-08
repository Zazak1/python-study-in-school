"""
游戏画面容器（Qt 嵌入占位）
用于展示游戏插件的 render 输出，便于后续接入 Arcade/Panda3D
"""
import json
from typing import Any, Dict

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame
from PySide6.QtCore import Qt

from ..styles.theme import CURRENT_THEME as t


class GameViewWidget(QFrame):
    """游戏渲染区域占位组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = QLabel("游戏画面")
        self._content = QTextEdit()
        self._content.setReadOnly(True)
        self._content.setPlaceholderText("等待游戏启动...（可嵌入 Arcade/Panda3D 窗口）")
        self._content.setMinimumHeight(300)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
            QTextEdit {{
                background: {t.bg_base};
                color: {t.text_display};
                border: none;
                font-family: Menlo, Consolas, monospace;
                font-size: 12px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._title.setStyleSheet(
            f"""
            font-size: 16px;
            font-weight: 700;
            color: {t.text_display};
            """
        )
        layout.addWidget(self._title)
        layout.addWidget(self._content, 1)

    def set_render_data(self, title: str, data: Dict[str, Any]):
        """更新渲染数据展示"""
        self._title.setText(title)
        try:
            formatted = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            formatted = str(data)
        self._content.setPlainText(formatted)

