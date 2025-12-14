"""
通用插件承载组件（MVP）

用于在没有专用 UI 的情况下展示插件 render 输出（JSON / 五子棋棋盘占位）。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QVBoxLayout

from client.plugins.base import GamePlugin
from .game_view import GameViewWidget


class PluginHostWidget(QFrame):
    def __init__(self, plugin: GamePlugin, game_type: str, title: Optional[str] = None, parent=None):
        super().__init__(parent)
        self._plugin = plugin
        self._game_type = game_type
        self._title = title or game_type

        self._view = GameViewWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view, 1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(100)

    def _tick(self):
        data: Any
        try:
            data = self._plugin.render(None)
        except Exception:
            data = {}

        if not isinstance(data, dict):
            data = {"value": str(data)}

        # 注入 game 字段，便于 GameViewWidget 选择渲染策略
        payload: Dict[str, Any] = {"game": self._game_type, **data}
        self._view.set_render_data(self._title, payload)

