"""
2D 射击游戏 UI（Qt 简易渲染版）

目的：提供可交互的 MVP 体验（WASD 移动、鼠标瞄准、左键射击）。
渲染使用 QPainter 绘制玩家与子弹的简化俯视图。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from PySide6.QtCore import Qt, QElapsedTimer, QTimer, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from client.plugins.base import GameState
from client.shell.styles.theme import CURRENT_THEME as t


@dataclass(frozen=True)
class _Viewport:
    scale: float
    offset_x: float
    offset_y: float

    def world_to_screen(self, x: float, y: float) -> QPointF:
        return QPointF(self.offset_x + x * self.scale, self.offset_y + y * self.scale)

    def screen_to_world(self, sx: float, sy: float) -> Tuple[float, float]:
        x = (sx - self.offset_x) / self.scale
        y = (sy - self.offset_y) / self.scale
        return x, y


class Shooter2DCanvas(QWidget):
    """绘制与输入层（焦点控件）。"""

    def __init__(self, plugin, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._plugin = plugin
        self._last_state: Dict[str, Any] = {}

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumSize(720, 420)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self._clock = QElapsedTimer()
        self._clock.start()

    def _tick(self):
        dt = float(self._clock.restart()) / 1000.0
        if dt <= 0:
            dt = 1 / 60

        # 仅在游戏中更新（并发送输入）
        try:
            if getattr(self._plugin, "state", None) == GameState.PLAYING:
                self._plugin.update(dt)
        except Exception:
            pass

        self.update()

    def _viewport(self) -> _Viewport:
        map_w = float(getattr(self._plugin, "MAP_WIDTH", 1920))
        map_h = float(getattr(self._plugin, "MAP_HEIGHT", 1080))

        w = max(1.0, float(self.width()))
        h = max(1.0, float(self.height()))

        scale = min(w / map_w, h / map_h)
        offset_x = (w - map_w * scale) / 2.0
        offset_y = (h - map_h * scale) / 2.0
        return _Viewport(scale=scale, offset_x=offset_x, offset_y=offset_y)

    def _clamp_world(self, x: float, y: float) -> Tuple[float, float]:
        map_w = float(getattr(self._plugin, "MAP_WIDTH", 1920))
        map_h = float(getattr(self._plugin, "MAP_HEIGHT", 1080))
        x = max(0.0, min(map_w, x))
        y = max(0.0, min(map_h, y))
        return x, y

    def _map_key(self, key: int) -> Optional[str]:
        mapping = {
            Qt.Key_W: "w",
            Qt.Key_A: "a",
            Qt.Key_S: "s",
            Qt.Key_D: "d",
            Qt.Key_Up: "up",
            Qt.Key_Left: "left",
            Qt.Key_Down: "down",
            Qt.Key_Right: "right",
        }
        return mapping.get(key)

    def keyPressEvent(self, event):
        mapped = self._map_key(event.key())
        if mapped:
            try:
                self._plugin.on_key_down(mapped)
            except Exception:
                pass
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        mapped = self._map_key(event.key())
        if mapped:
            try:
                self._plugin.on_key_up(mapped)
            except Exception:
                pass
            event.accept()
            return
        super().keyReleaseEvent(event)

    def mouseMoveEvent(self, event):
        vp = self._viewport()
        x, y = vp.screen_to_world(event.position().x(), event.position().y())
        x, y = self._clamp_world(x, y)
        try:
            self._plugin.on_mouse_move(int(x), int(y))
        except Exception:
            pass
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            vp = self._viewport()
            x, y = vp.screen_to_world(event.position().x(), event.position().y())
            x, y = self._clamp_world(x, y)
            try:
                self._plugin.on_mouse_down(1, int(x), int(y))
            except Exception:
                pass
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景
        painter.fillRect(self.rect(), QColor(t.bg_base))

        # 拉取状态
        try:
            data = self._plugin.render(None)
            if isinstance(data, dict):
                self._last_state = data
        except Exception:
            pass

        data = self._last_state or {}
        vp = self._viewport()

        map_w = float(getattr(self._plugin, "MAP_WIDTH", 1920))
        map_h = float(getattr(self._plugin, "MAP_HEIGHT", 1080))
        map_rect = (
            vp.offset_x,
            vp.offset_y,
            map_w * vp.scale,
            map_h * vp.scale,
        )

        # 地图边框
        painter.setPen(QPen(QColor(t.border_normal), 2))
        painter.setBrush(QBrush(QColor(t.bg_card)))
        painter.drawRoundedRect(*map_rect, 14, 14)

        # 玩家
        players = data.get("players") or []
        bullets = data.get("bullets") or []
        local_id = data.get("local_player_id") or ""

        def team_color(team_id: int, is_local: bool) -> QColor:
            if is_local:
                return QColor(t.primary)
            return QColor("#EF4444" if (team_id % 2) else "#22C55E")

        radius = 18.0 * vp.scale
        for p in players:
            if not isinstance(p, dict):
                continue
            x = float(p.get("x") or 0.0)
            y = float(p.get("y") or 0.0)
            is_alive = bool(p.get("is_alive", True))
            user_id = str(p.get("user_id") or "")
            is_local = user_id == local_id
            team_id = int(p.get("team_id") or p.get("team") or 0)
            rot = float(p.get("rotation") or 0.0)
            hp = int(p.get("health") or 0)

            pos = vp.world_to_screen(x, y)
            fill = team_color(team_id, is_local)
            if not is_alive:
                fill = QColor("#64748B")

            painter.setPen(QPen(QColor("#0F172A"), 2))
            painter.setBrush(QBrush(fill))
            painter.drawEllipse(pos, radius, radius)

            # 朝向线
            import math

            rad = math.radians(rot)
            dir_x, dir_y = math.cos(rad), math.sin(rad)
            tip = QPointF(pos.x() + dir_x * radius * 1.6, pos.y() + dir_y * radius * 1.6)
            painter.setPen(QPen(QColor("#0F172A"), 3))
            painter.drawLine(pos, tip)

            # 血量条
            bar_w = max(30.0, radius * 2.2)
            bar_h = 6.0
            bx = pos.x() - bar_w / 2
            by = pos.y() - radius - 14
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#111827"))
            painter.drawRoundedRect(bx, by, bar_w, bar_h, 3, 3)
            ratio = max(0.0, min(1.0, hp / 100.0))
            painter.setBrush(QColor("#22C55E" if ratio > 0.5 else "#F59E0B" if ratio > 0.25 else "#EF4444"))
            painter.drawRoundedRect(bx, by, bar_w * ratio, bar_h, 3, 3)

        # 子弹
        b_radius = 6.0 * vp.scale
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#E5E7EB"))
        for b in bullets:
            if not isinstance(b, dict):
                continue
            x = float(b.get("x") or 0.0)
            y = float(b.get("y") or 0.0)
            pos = vp.world_to_screen(x, y)
            painter.drawEllipse(pos, b_radius, b_radius)

        # 右上角提示
        painter.setPen(QColor(t.text_caption))
        painter.setFont(QFont("Menlo", 10))
        hint = "WASD/方向键移动 · 鼠标瞄准 · 左键射击"
        painter.drawText(self.rect().adjusted(12, 8, -12, -8), Qt.AlignTop | Qt.AlignRight, hint)


class Shooter2DWidget(QFrame):
    """2D 射击整体 UI：顶部状态 + 画布。"""

    def __init__(self, plugin, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._plugin = plugin

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_base};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
            """
        )

        self._title = QLabel("2D 射击")
        self._title.setStyleSheet(f"color: {t.text_display}; font-size: 16px; font-weight: 900;")
        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {t.text_caption}; font-size: 12px; font-weight: 700;")

        header = QHBoxLayout()
        header.setContentsMargins(16, 14, 16, 0)
        header.addWidget(self._title)
        header.addStretch()
        header.addWidget(self._status)

        self._canvas = Shooter2DCanvas(plugin=plugin)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addLayout(header)
        root.addWidget(self._canvas, 1)

        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._refresh)
        self._ui_timer.start(250)

        QTimer.singleShot(50, self._canvas.setFocus)

    def _refresh(self):
        try:
            state = getattr(self._plugin, "state", None)
            self._status.setText(f"状态: {state.name if state else '-'}")
        except Exception:
            self._status.setText("")

