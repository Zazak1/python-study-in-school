"""
大富翁 UI（Qt 简易版）

提供 MVP 交互：
- 掷骰子 / 买地 / 结束回合
- 简易棋盘展示（横向 1 行格子）
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from client.shell.styles.theme import CURRENT_THEME as t


class MonopolyBoardCanvas(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._state: Dict[str, Any] = {}
        self.setMinimumHeight(140)

    def set_state(self, state: Dict[str, Any]):
        self._state = state or {}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(t.bg_base))

        tiles = self._state.get("tiles") or []
        players = self._state.get("players") or {}
        current_player = str(self._state.get("current_player") or "")
        my_user_id = str(self._state.get("my_user_id") or "")

        if not isinstance(tiles, list) or not tiles:
            painter.setPen(QColor(t.text_caption))
            painter.drawText(self.rect(), Qt.AlignCenter, "等待棋盘数据…")
            return

        w = float(self.width())
        h = float(self.height())
        margin = 10.0
        gap = 6.0
        tile_h = max(110.0, h - margin * 2)
        tile_w = (w - margin * 2 - gap * (len(tiles) - 1)) / max(1, len(tiles))
        y = (h - tile_h) / 2.0

        # 预处理：tile_id -> players list
        players_on: Dict[int, list[str]] = {}
        if isinstance(players, dict):
            for uid, st in players.items():
                if not isinstance(st, dict):
                    continue
                pos = st.get("position")
                if isinstance(pos, int):
                    players_on.setdefault(pos, []).append(str(uid))

        def tile_color(ttype: str) -> QColor:
            colors = {
                "start": QColor("#22C55E"),
                "property": QColor("#3B82F6"),
                "tax": QColor("#EF4444"),
                "chance": QColor("#A855F7"),
                "chest": QColor("#A855F7"),
                "station": QColor("#F59E0B"),
            }
            return colors.get(ttype, QColor("#64748B"))

        painter.setFont(QFont("PingFang SC", 10))
        for idx, tile in enumerate(tiles):
            if not isinstance(tile, dict):
                continue
            x = margin + idx * (tile_w + gap)
            rect = QRectF(x, y, tile_w, tile_h)

            ttype = str(tile.get("type") or "")
            name = str(tile.get("name") or f"#{idx}")
            owner = tile.get("owner")
            owner_text = str(owner) if owner else ""

            # 卡片
            painter.setPen(QPen(QColor(t.border_normal), 1))
            painter.setBrush(QBrush(QColor(t.bg_card)))
            painter.drawRoundedRect(rect, 12, 12)

            # 顶部条（类型色）
            header = QRectF(rect.x(), rect.y(), rect.width(), 18)
            painter.setPen(Qt.NoPen)
            painter.setBrush(tile_color(ttype))
            painter.drawRoundedRect(header, 12, 12)

            # 名称
            painter.setPen(QColor(t.text_display))
            painter.drawText(
                QRectF(rect.x() + 8, rect.y() + 22, rect.width() - 16, 34),
                Qt.TextWordWrap,
                name,
            )

            # 归属
            if owner_text:
                painter.setPen(QColor(t.text_caption))
                painter.setFont(QFont("Menlo", 9))
                painter.drawText(
                    QRectF(rect.x() + 8, rect.y() + 58, rect.width() - 16, 16),
                    Qt.AlignLeft | Qt.AlignVCenter,
                    f"owner: {owner_text[:8]}",
                )

            # 当前玩家高亮
            is_current_tile = False
            if isinstance(players, dict) and current_player and current_player in players:
                cp = players[current_player]
                if isinstance(cp, dict) and cp.get("position") == idx:
                    is_current_tile = True
            if is_current_tile:
                painter.setPen(QPen(QColor(t.primary), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 12, 12)

            # 玩家棋子
            uids = players_on.get(idx, [])
            if uids:
                r = 6.0
                start_x = rect.x() + 10
                base_y = rect.y() + rect.height() - 16
                for i, uid in enumerate(uids[:6]):
                    color = QColor(t.primary if uid == my_user_id else "#E5E7EB")
                    painter.setPen(QPen(QColor("#0F172A"), 1))
                    painter.setBrush(QBrush(color))
                    painter.drawEllipse(QPointF(start_x + i * (r * 2 + 4), base_y), r, r)


class MonopolyWidget(QFrame):
    def __init__(self, plugin, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._plugin = plugin
        self._last_state: Dict[str, Any] = {}

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_base};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
            QPushButton {{
                border-radius: 10px;
                font-weight: 800;
                padding: 10px 14px;
            }}
            """
        )

        self._title = QLabel("大富翁")
        self._title.setStyleSheet(f"color: {t.text_display}; font-size: 16px; font-weight: 900;")

        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {t.text_caption}; font-size: 12px; font-weight: 700;")

        header = QHBoxLayout()
        header.setContentsMargins(16, 14, 16, 0)
        header.addWidget(self._title)
        header.addStretch()
        header.addWidget(self._status)

        self._board = MonopolyBoardCanvas()

        self._players = QLabel("")
        self._players.setWordWrap(True)
        self._players.setStyleSheet(f"color: {t.text_body}; font-size: 12px;")

        self._event = QLabel("")
        self._event.setWordWrap(True)
        self._event.setStyleSheet(f"color: {t.text_caption}; font-size: 12px;")

        # 操作按钮
        self._btn_roll = QPushButton("🎲 掷骰子")
        self._btn_buy = QPushButton("🏠 买地")
        self._btn_end = QPushButton("⏭️ 结束回合")

        self._btn_roll.clicked.connect(lambda: self._safe_call(getattr(self._plugin, "roll_dice", None)))
        self._btn_buy.clicked.connect(lambda: self._safe_call(getattr(self._plugin, "buy_property", None)))
        self._btn_end.clicked.connect(lambda: self._safe_call(getattr(self._plugin, "end_turn", None)))

        buttons = QHBoxLayout()
        buttons.setContentsMargins(16, 0, 16, 16)
        buttons.setSpacing(10)
        buttons.addWidget(self._btn_roll)
        buttons.addWidget(self._btn_buy)
        buttons.addWidget(self._btn_end)
        buttons.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addLayout(header)
        root.addWidget(self._board, 0)
        root.addWidget(self._players, 0)
        root.addWidget(self._event, 0)
        root.addLayout(buttons)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(150)

    def _safe_call(self, fn):
        if not fn:
            return
        try:
            fn()
        except Exception:
            return

    def _refresh(self):
        try:
            data = self._plugin.render(None)
            if isinstance(data, dict):
                self._last_state = data
        except Exception:
            pass

        state = self._last_state or {}
        self._board.set_state(state)

        phase = str(state.get("phase") or "")
        current_player = str(state.get("current_player") or "")
        dice = state.get("dice") or (0, 0)
        is_my_turn = bool(state.get("is_my_turn", False))
        my_user_id = str(state.get("my_user_id") or "")

        dice_text = ""
        if isinstance(dice, (list, tuple)) and len(dice) == 2:
            dice_text = f"{dice[0]}+{dice[1]}"

        self._status.setText(f"阶段: {phase} · 当前回合: {current_player or '-'} · 骰子: {dice_text or '-'}")

        # 玩家信息
        players = state.get("players") or {}
        if isinstance(players, dict) and players:
            lines = []
            for uid, p in players.items():
                if not isinstance(p, dict):
                    continue
                money = p.get("money")
                pos = p.get("position")
                props = p.get("properties") or []
                mark = " (我)" if str(uid) == my_user_id else ""
                mark2 = " ⭐" if str(uid) == current_player else ""
                lines.append(
                    f"{uid}{mark}{mark2} · 💰{money} · 📍{pos} · 🏠{len(props)}"
                )
            self._players.setText("玩家：\n" + "\n".join(lines))
        else:
            self._players.setText("")

        # 事件摘要
        last_event = state.get("last_event") or {}
        summary = ""
        if isinstance(last_event, dict) and last_event:
            parts = []
            if last_event.get("tax"):
                parts.append(f"缴税 -{last_event.get('tax')}")
            pay_rent = last_event.get("pay_rent")
            if isinstance(pay_rent, dict):
                parts.append(f"付租金 -> {pay_rent.get('to')} (-{pay_rent.get('amount')})")
            card = last_event.get("card")
            if isinstance(card, dict):
                amount = card.get("amount")
                sign = "+" if isinstance(amount, int) and amount > 0 else ""
                parts.append(f"{card.get('desc') or card.get('type')}: {sign}{amount}")
            if last_event.get("passed_start"):
                parts.append("经过起点 +2000")
            if last_event.get("action"):
                parts.append(f"action={last_event.get('action')}")
            summary = " · ".join([str(p) for p in parts if p])
        self._event.setText(summary)

        # 按钮可用性
        self._btn_roll.setEnabled(is_my_turn and phase == "rolling")

        can_buy = False
        if is_my_turn and phase == "action" and isinstance(players, dict):
            mine = players.get(my_user_id)
            if isinstance(mine, dict):
                pos = mine.get("position")
                money = int(mine.get("money") or 0)
                tiles = state.get("tiles") or []
                if isinstance(pos, int) and isinstance(tiles, list) and 0 <= pos < len(tiles):
                    tile = tiles[pos]
                    if isinstance(tile, dict) and str(tile.get("type") or "") == "property" and not tile.get("owner"):
                        price = int(tile.get("price") or 0)
                        can_buy = money >= price > 0
        self._btn_buy.setEnabled(can_buy)

        self._btn_end.setEnabled(is_my_turn and phase in {"action", "end_turn"})
