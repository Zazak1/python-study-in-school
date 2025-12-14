"""
游戏画面容器（Qt 嵌入占位）
用于展示游戏插件的 render 输出，便于后续接入 Arcade/Panda3D
"""
import json
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QFrame
from PySide6.QtCore import Qt

from ..styles.theme import CURRENT_THEME as t
from client.plugins.gomoku.widget import GomokuBoard


class GameViewWidget(QFrame):
    """游戏渲染区域占位组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = QLabel("游戏画面")
        self._content = QTextEdit()
        self._content.setReadOnly(True)
        self._content.setPlaceholderText("等待游戏启动...（可嵌入 Arcade/Panda3D 窗口）")
        self._content.setMinimumHeight(300)

        # 五子棋棋盘展示（默认为隐藏，占位）
        self._gomoku_board = GomokuBoard()
        self._gomoku_board.hide()

        # 状态说明
        self._info = QLabel("")
        self._info.setWordWrap(True)
        self._info.setStyleSheet(f"color: {t.text_caption}; font-size: 12px;")

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
        layout.addWidget(self._gomoku_board, 0, alignment=Qt.AlignCenter)
        layout.addWidget(self._info)
        layout.addWidget(self._content, 1)

    def set_render_data(self, title: str, data: Dict[str, Any]):
        """更新渲染数据展示"""
        self._title.setText(title)

        game_type = data.get("game")
        if game_type == "gomoku":
            self._render_gomoku(data)
        else:
            self._render_json(data)

    # ========== 渲染策略 ==========
    def _render_json(self, data: Dict[str, Any]):
        """默认 JSON 展示"""
        self._gomoku_board.hide()
        self._info.setText("")
        self._content.show()

        try:
            formatted = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception:
            formatted = str(data)
        self._content.setPlainText(formatted)

    def _render_gomoku(self, data: Dict[str, Any]):
        """绘制五子棋棋盘"""
        self._content.hide()
        self._gomoku_board.show()

        board: Optional[List[List[int]]] = data.get("board")
        size = data.get("board_size", 15)
        if not board:
            board = [[0] * size for _ in range(size)]

        self._gomoku_board.set_board(board)

        current_player = data.get("current_player", 1)
        if isinstance(current_player, str):
            current_player = 1 if current_player.lower() == "black" else 2

        my_color = data.get("my_color", 1)
        if my_color not in (1, 2):
            my_color = 1

        last_move: Optional[Tuple[int, int]] = None
        if isinstance(data.get("last_move"), (list, tuple)) and len(data["last_move"]) == 2:
            last_move = (data["last_move"][0], data["last_move"][1])

        winner = data.get("winner", 0) or 0

        self._gomoku_board.set_state(
            current_player=current_player,
            my_color=my_color,
            last_move=last_move,
            winner=winner,
        )

        # 状态摘要
        status_parts = []
        if data.get("status"):
            status_parts.append(str(data["status"]))
        if data.get("frame") is not None:
            status_parts.append(f"帧: {data['frame']}")
        if last_move:
            status_parts.append(f"最后落子: {last_move[0]}, {last_move[1]}")

        self._info.setText(" · ".join(status_parts))

