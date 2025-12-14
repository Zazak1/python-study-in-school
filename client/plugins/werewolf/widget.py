"""
狼人杀 UI（Qt MVP）

提供基础交互：
- 夜晚：狼人击杀 / 预言家查验
- 投票：选择目标并投票
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from client.shell.styles.theme import CURRENT_THEME as t


class WerewolfWidget(QFrame):
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

        self._title = QLabel("狼人杀")
        self._title.setStyleSheet(f"color: {t.text_display}; font-size: 16px; font-weight: 900;")
        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {t.text_caption}; font-size: 12px; font-weight: 700;")

        header = QHBoxLayout()
        header.setContentsMargins(16, 14, 16, 0)
        header.addWidget(self._title)
        header.addStretch()
        header.addWidget(self._status)

        self._role = QLabel("身份：-")
        self._role.setStyleSheet(f"color: {t.text_body}; font-size: 12px; font-weight: 800;")
        self._seer = QLabel("")
        self._seer.setWordWrap(True)
        self._seer.setStyleSheet(f"color: {t.text_caption}; font-size: 12px;")

        self._players = QListWidget()
        self._players.setStyleSheet(
            f"""
            QListWidget {{
                background: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 12px;
                padding: 6px;
                color: {t.text_display};
            }}
            """
        )

        self._btn_kill = QPushButton("🐺 击杀")
        self._btn_check = QPushButton("🔮 查验")
        self._btn_vote = QPushButton("🗳️ 投票")

        self._btn_kill.clicked.connect(self._on_kill)
        self._btn_check.clicked.connect(self._on_check)
        self._btn_vote.clicked.connect(self._on_vote)

        actions = QHBoxLayout()
        actions.setContentsMargins(16, 0, 16, 16)
        actions.setSpacing(10)
        actions.addWidget(self._btn_kill)
        actions.addWidget(self._btn_check)
        actions.addWidget(self._btn_vote)
        actions.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addLayout(header)

        info = QVBoxLayout()
        info.setContentsMargins(16, 0, 16, 0)
        info.setSpacing(6)
        info.addWidget(self._role)
        info.addWidget(self._seer)
        root.addLayout(info)

        root.addWidget(self._players, 1)
        root.addLayout(actions)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(200)

        self._players.itemSelectionChanged.connect(self._refresh_buttons)

    def _selected_user_id(self) -> Optional[str]:
        item = self._players.currentItem()
        if not item:
            return None
        uid = item.data(Qt.UserRole)
        return str(uid) if uid else None

    def _safe_call(self, fn, *args):
        if not fn:
            return
        try:
            fn(*args)
        except Exception:
            return

    def _on_kill(self):
        uid = self._selected_user_id()
        if not uid:
            return
        self._safe_call(getattr(self._plugin, "wolf_kill", None), uid)

    def _on_check(self):
        uid = self._selected_user_id()
        if not uid:
            return
        self._safe_call(getattr(self._plugin, "seer_check", None), uid)

    def _on_vote(self):
        uid = self._selected_user_id()
        if not uid:
            return
        self._safe_call(getattr(self._plugin, "vote", None), uid)

    def _refresh(self):
        try:
            data = self._plugin.render(None)
            if isinstance(data, dict):
                self._last_state = data
        except Exception:
            pass

        state = self._last_state or {}
        phase = str(state.get("phase") or "")
        day = int(state.get("day") or 0)
        timer = state.get("timer")
        try:
            timer_s = float(timer) if timer is not None else 0.0
        except Exception:
            timer_s = 0.0

        my_role = state.get("my_role")
        my_user_id = str(state.get("my_user_id") or "")

        self._status.setText(f"阶段: {phase} · 第{day}天 · 倒计时: {timer_s:.0f}s")
        self._role.setText(f"身份：{my_role or '-'} · 我：{my_user_id or '-'}")

        # 预言家结果
        seer = state.get("seer_result")
        if isinstance(seer, dict) and seer.get("target"):
            self._seer.setText(
                f"查验结果：{seer.get('target')} 是 {'狼人' if seer.get('is_wolf') else '好人'}"
            )
        else:
            self._seer.setText("")

        # 更新玩家列表
        selected = self._selected_user_id()
        players = state.get("players") or {}
        if isinstance(players, dict):
            self._players.blockSignals(True)
            self._players.clear()
            for uid, p in players.items():
                if not isinstance(p, dict):
                    continue
                alive = bool(p.get("alive", True))
                text = f"{uid} {'(存活)' if alive else '(死亡)'}"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, str(uid))
                if not alive:
                    item.setForeground(QColor(t.text_placeholder))
                elif str(uid) == my_user_id:
                    item.setForeground(QColor(t.primary))
                self._players.addItem(item)
                if selected and str(uid) == selected:
                    self._players.setCurrentItem(item)
            self._players.blockSignals(False)

        self._refresh_buttons()

    def _refresh_buttons(self):
        state = self._last_state or {}
        phase = str(state.get("phase") or "")
        my_role = str(state.get("my_role") or "")

        uid = self._selected_user_id()
        players = state.get("players") or {}
        alive_selected = False
        if uid and isinstance(players, dict):
            p = players.get(uid)
            alive_selected = bool(p.get("alive", True)) if isinstance(p, dict) else False

        can_kill = my_role == "werewolf" and phase == "night"
        can_check = my_role == "seer" and phase == "night"
        can_vote = phase == "vote"

        self._btn_kill.setEnabled(bool(uid and alive_selected and can_kill))
        self._btn_check.setEnabled(bool(uid and alive_selected and can_check))
        self._btn_vote.setEnabled(bool(uid and alive_selected and can_vote))

