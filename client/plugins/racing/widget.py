"""
赛车竞速 UI（Qt MVP）

说明：
- 俯视 2D 展示（x-z 平面） + 简易输入控件（油门/刹车/转向）
- 键盘快捷：W=油门，S=刹车，A/D=转向
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from client.shell.styles.theme import CURRENT_THEME as t


@dataclass(frozen=True)
class _Bounds:
    min_x: float
    max_x: float
    min_z: float
    max_z: float


class RacingTrackCanvas(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._state: Dict[str, Any] = {}
        self.setMinimumHeight(420)

    def set_state(self, state: Dict[str, Any]):
        self._state = state or {}
        self.update()

    def _collect_points(self, track: Dict[str, Any], cars: Dict[str, Any]) -> Iterable[Tuple[float, float]]:
        cps = track.get("checkpoints") or []
        for cp in cps:
            if isinstance(cp, (list, tuple)) and len(cp) >= 3:
                yield float(cp[0]), float(cp[2])
        starts = track.get("start_positions") or []
        for sp in starts:
            if isinstance(sp, (list, tuple)) and len(sp) >= 3:
                yield float(sp[0]), float(sp[2])
        if isinstance(cars, dict):
            for st in cars.values():
                if not isinstance(st, dict):
                    continue
                pos = st.get("pos")
                if isinstance(pos, dict):
                    yield float(pos.get("x") or 0.0), float(pos.get("z") or 0.0)

    def _bounds(self) -> _Bounds:
        track = self._state.get("track") or {}
        cars = self._state.get("cars") or {}
        pts = list(self._collect_points(track if isinstance(track, dict) else {}, cars if isinstance(cars, dict) else {}))
        if not pts:
            return _Bounds(min_x=-10, max_x=60, min_z=-20, max_z=20)
        xs = [p[0] for p in pts]
        zs = [p[1] for p in pts]
        min_x, max_x = min(xs), max(xs)
        min_z, max_z = min(zs), max(zs)
        pad_x = max(5.0, (max_x - min_x) * 0.15)
        pad_z = max(5.0, (max_z - min_z) * 0.15)
        return _Bounds(min_x=min_x - pad_x, max_x=max_x + pad_x, min_z=min_z - pad_z, max_z=max_z + pad_z)

    def _world_to_screen(self, x: float, z: float, rect: QRectF, bounds: _Bounds) -> QPointF:
        bw = max(1e-6, bounds.max_x - bounds.min_x)
        bh = max(1e-6, bounds.max_z - bounds.min_z)
        sx = rect.left() + (x - bounds.min_x) / bw * rect.width()
        sy = rect.top() + (z - bounds.min_z) / bh * rect.height()
        return QPointF(sx, sy)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(t.bg_base))

        state = self._state or {}
        track = state.get("track") if isinstance(state.get("track"), dict) else {}
        cars = state.get("cars") if isinstance(state.get("cars"), dict) else {}
        my_user_id = str(state.get("my_user_id") or "")

        bounds = self._bounds()
        margin = 12.0
        rect = QRectF(margin, margin, max(1.0, self.width() - margin * 2), max(1.0, self.height() - margin * 2))

        # 背景卡片
        painter.setPen(QPen(QColor(t.border_normal), 2))
        painter.setBrush(QBrush(QColor(t.bg_card)))
        painter.drawRoundedRect(rect, 16, 16)

        # 赛道线（连接 checkpoints）
        cps = track.get("checkpoints") or []
        points = []
        for cp in cps:
            if isinstance(cp, (list, tuple)) and len(cp) >= 3:
                points.append(self._world_to_screen(float(cp[0]), float(cp[2]), rect, bounds))
        if len(points) >= 2:
            painter.setPen(QPen(QColor("#94A3B8"), 3))
            for i in range(len(points)):
                a = points[i]
                b = points[(i + 1) % len(points)]
                painter.drawLine(a, b)

        # checkpoints 标记
        painter.setFont(QFont("Menlo", 9))
        for i, p in enumerate(points):
            painter.setPen(QPen(QColor("#0F172A"), 1))
            painter.setBrush(QBrush(QColor("#E2E8F0")))
            painter.drawEllipse(p, 6, 6)
            painter.setPen(QColor("#0F172A"))
            painter.drawText(QRectF(p.x() + 8, p.y() - 10, 40, 20), Qt.AlignLeft | Qt.AlignVCenter, str(i))

        # cars
        import math

        painter.setFont(QFont("Menlo", 10))
        for uid, st in cars.items():
            if not isinstance(st, dict):
                continue
            pos = st.get("pos") if isinstance(st.get("pos"), dict) else {}
            x = float(pos.get("x") or 0.0)
            z = float(pos.get("z") or 0.0)
            rot = float(st.get("rotation") or 0.0)
            finished = bool(st.get("finished") or False)
            rank = int(st.get("rank") or 0)

            p = self._world_to_screen(x, z, rect, bounds)
            color = QColor(t.primary if str(uid) == my_user_id else "#E5E7EB")
            if finished:
                color = QColor("#94A3B8")

            # 画个小三角指示朝向（rot 为弧度，dir=(sin,cos)）
            dx = math.sin(rot)
            dz = math.cos(rot)
            tip = QPointF(p.x() + dx * 14, p.y() + dz * 14)
            left = QPointF(p.x() - dz * 8, p.y() + dx * 8)
            right = QPointF(p.x() + dz * 8, p.y() - dx * 8)

            painter.setPen(QPen(QColor("#0F172A"), 1))
            painter.setBrush(QBrush(color))
            painter.drawPolygon([tip, left, right])

            label = f"{uid}"
            if rank:
                label += f" #{rank}"
            painter.setPen(QColor(t.text_display))
            painter.drawText(QRectF(p.x() + 10, p.y() - 12, 140, 22), Qt.AlignLeft | Qt.AlignVCenter, label)


class RacingWidget(QFrame):
    def __init__(self, plugin, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._plugin = plugin
        self._last_state: Dict[str, Any] = {}
        self._keys: set[str] = set()
        self._last_sent: Tuple[float, float, float] = (-1.0, -1.0, -2.0)

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {t.bg_base};
                border: 1px solid {t.border_light};
                border-radius: 16px;
            }}
            """
        )

        self.setFocusPolicy(Qt.StrongFocus)

        self._title = QLabel("赛车竞速")
        self._title.setStyleSheet(f"color: {t.text_display}; font-size: 16px; font-weight: 900;")
        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {t.text_caption}; font-size: 12px; font-weight: 700;")

        header = QHBoxLayout()
        header.setContentsMargins(16, 14, 16, 0)
        header.addWidget(self._title)
        header.addStretch()
        header.addWidget(self._status)

        self._canvas = RacingTrackCanvas()

        # 控件区（滑条）
        self._slider_throttle = QSlider(Qt.Horizontal)
        self._slider_throttle.setRange(0, 100)
        self._slider_throttle.setValue(0)

        self._slider_brake = QSlider(Qt.Horizontal)
        self._slider_brake.setRange(0, 100)
        self._slider_brake.setValue(0)

        self._slider_steering = QSlider(Qt.Horizontal)
        self._slider_steering.setRange(-100, 100)
        self._slider_steering.setValue(0)

        self._lbl_throttle = QLabel("油门: 0%")
        self._lbl_brake = QLabel("刹车: 0%")
        self._lbl_steering = QLabel("转向: 0%")
        for lbl in (self._lbl_throttle, self._lbl_brake, self._lbl_steering):
            lbl.setStyleSheet(f"color: {t.text_body}; font-size: 12px; font-weight: 800;")

        self._slider_throttle.valueChanged.connect(lambda v: self._lbl_throttle.setText(f"油门: {v}%"))
        self._slider_brake.valueChanged.connect(lambda v: self._lbl_brake.setText(f"刹车: {v}%"))
        self._slider_steering.valueChanged.connect(lambda v: self._lbl_steering.setText(f"转向: {v}%"))

        controls = QFrame()
        controls.setStyleSheet(
            f"""
            QFrame {{
                background: {t.bg_card};
                border: 1px solid {t.border_light};
                border-radius: 12px;
            }}
            """
        )
        grid = QGridLayout(controls)
        grid.setContentsMargins(12, 10, 12, 12)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.addWidget(self._lbl_throttle, 0, 0)
        grid.addWidget(self._slider_throttle, 0, 1)
        grid.addWidget(self._lbl_brake, 1, 0)
        grid.addWidget(self._slider_brake, 1, 1)
        grid.addWidget(self._lbl_steering, 2, 0)
        grid.addWidget(self._slider_steering, 2, 1)
        hint = QLabel("键盘：W=油门，S=刹车，A/D=转向（覆盖滑条）")
        hint.setStyleSheet(f"color: {t.text_caption}; font-size: 12px;")
        grid.addWidget(hint, 3, 0, 1, 2)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addLayout(header)
        root.addWidget(self._canvas, 1)
        root.addWidget(controls, 0)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_state)
        self._refresh_timer.start(120)

        self._input_timer = QTimer(self)
        self._input_timer.timeout.connect(self._send_input)
        self._input_timer.start(50)

        QTimer.singleShot(50, self.setFocus)

    def keyPressEvent(self, event):
        key = event.key()
        mapping = {Qt.Key_W: "w", Qt.Key_A: "a", Qt.Key_S: "s", Qt.Key_D: "d"}
        mapped = mapping.get(key)
        if mapped:
            self._keys.add(mapped)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        key = event.key()
        mapping = {Qt.Key_W: "w", Qt.Key_A: "a", Qt.Key_S: "s", Qt.Key_D: "d"}
        mapped = mapping.get(key)
        if mapped:
            self._keys.discard(mapped)
            event.accept()
            return
        super().keyReleaseEvent(event)

    def _refresh_state(self):
        try:
            data = self._plugin.render(None)
            if isinstance(data, dict):
                self._last_state = data
        except Exception:
            pass

        state = self._last_state or {}
        self._canvas.set_state(state)

        s = str(state.get("state") or "")
        race_time = float(state.get("race_time") or 0.0)
        countdown = float(state.get("countdown") or 0.0)
        self._status.setText(f"状态: {s} · 时间: {race_time:.1f}s · 倒计时: {countdown:.0f}")

    def _send_input(self):
        # 读取滑条输入
        throttle = float(self._slider_throttle.value()) / 100.0
        brake = float(self._slider_brake.value()) / 100.0
        steering = float(self._slider_steering.value()) / 100.0

        # 键盘覆盖
        if "w" in self._keys:
            throttle = 1.0
        if "s" in self._keys:
            brake = 1.0
        if "a" in self._keys and "d" not in self._keys:
            steering = -1.0
        elif "d" in self._keys and "a" not in self._keys:
            steering = 1.0

        # 去抖：减少网络发送
        last = self._last_sent
        now = (round(throttle, 2), round(brake, 2), round(steering, 2))
        if now == last:
            return

        self._last_sent = now
        try:
            self._plugin.set_input(throttle=throttle, brake=brake, steering=steering)
        except Exception:
            return

