"""
赛车竞速游戏插件（客户端，MVP）

权威逻辑在服务器端 `server/games/racing.py`：
- countdown -> racing -> finished
- tick_rate = 30 帧同步广播 game_sync
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..base import EventType, GameContext, GamePlugin, GameState, NetworkEvent, RoomState


@dataclass
class CarState:
    user_id: str
    nickname: str = ""
    pos: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    vel: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    rotation: float = 0.0
    lap: int = 0
    checkpoint: int = 0
    rank: int = 0
    finished: bool = False


class RacingPlugin(GamePlugin):
    PLUGIN_NAME = "racing"
    PLUGIN_VERSION = "0.1.0"
    PLUGIN_DESCRIPTION = "赛车竞速（MVP：服务器权威物理）"
    MIN_PLAYERS = 2
    MAX_PLAYERS = 6
    SUPPORTS_SPECTATE = True

    def __init__(self):
        super().__init__()
        self._cars: Dict[str, CarState] = {}
        self._track: Dict[str, Any] = {}
        self._race_state: str = "waiting"
        self._race_time: float = 0.0
        self._countdown: float = 0.0

        self._my_user_id: str = ""
        self._input: Dict[str, float] = {"throttle": 0.0, "brake": 0.0, "steering": 0.0}

    def load(self, context: GameContext) -> bool:
        self._context = context
        self._state = GameState.LOADING

        if context.local_user:
            self._my_user_id = context.local_user.user_id

        self._cars.clear()
        self._track = {}
        self._race_state = "waiting"
        self._race_time = 0.0
        self._countdown = 0.0
        self._input = {"throttle": 0.0, "brake": 0.0, "steering": 0.0}

        self._state = GameState.READY
        self._is_loaded = True
        return True

    def join_room(self, room_state: RoomState) -> bool:
        self._room_state = room_state
        for p in room_state.current_players:
            self._cars.setdefault(p.user_id, CarState(user_id=p.user_id, nickname=p.nickname))
        return True

    def start_game(self) -> bool:
        self._state = GameState.PLAYING
        return True

    def dispose(self) -> None:
        self._cars.clear()
        self._track = {}
        self._race_state = "waiting"
        self._race_time = 0.0
        self._countdown = 0.0
        self._input = {"throttle": 0.0, "brake": 0.0, "steering": 0.0}
        self._state = GameState.IDLE
        self._is_loaded = False

    def update(self, dt: float) -> None:
        # MVP：输入由 UI 调用 set_input 触发发送
        return

    def render(self, surface: Any) -> Dict[str, Any]:
        return {
            "state": self._race_state,
            "race_time": self._race_time,
            "countdown": self._countdown,
            "track": self._track,
            "cars": {
                uid: {
                    "pos": c.pos,
                    "vel": c.vel,
                    "rotation": c.rotation,
                    "lap": c.lap,
                    "checkpoint": c.checkpoint,
                    "rank": c.rank,
                    "finished": c.finished,
                }
                for uid, c in self._cars.items()
            },
            "my_user_id": self._my_user_id,
        }

    def on_network(self, event: NetworkEvent) -> None:
        if event.type == EventType.SYNC:
            self._apply_state(event.payload or {})
            return

        if event.type == EventType.STATE:
            payload = event.payload or {}
            action = payload.get("action")
            if action == "game_start":
                self._apply_state(payload)
            return

    # ========== 输入 ==========
    def set_input(self, throttle: float, brake: float, steering: float):
        throttle = max(0.0, min(1.0, float(throttle)))
        brake = max(0.0, min(1.0, float(brake)))
        steering = max(-1.0, min(1.0, float(steering)))

        self._input = {"throttle": throttle, "brake": brake, "steering": steering}
        self.send_input({"action": "game_input", **self._input})

    # ========== 内部 ==========
    def _apply_state(self, state: Dict[str, Any]):
        self._race_state = str(state.get("state") or self._race_state)
        self._race_time = float(state.get("race_time") or self._race_time)
        self._countdown = float(state.get("countdown") or self._countdown)
        track = state.get("track")
        if isinstance(track, dict):
            self._track = track

        cars = state.get("cars")
        if isinstance(cars, list):
            for c in cars:
                if not isinstance(c, dict):
                    continue
                uid = c.get("user_id")
                if not uid:
                    continue
                uid = str(uid)
                car = self._cars.setdefault(uid, CarState(user_id=uid))
                car.nickname = str(c.get("nickname") or car.nickname)
                if isinstance(c.get("pos"), dict):
                    car.pos = c["pos"]
                if isinstance(c.get("vel"), dict):
                    car.vel = c["vel"]
                car.rotation = float(c.get("rotation") or car.rotation)
                car.lap = int(c.get("lap") or car.lap)
                car.checkpoint = int(c.get("checkpoint") or car.checkpoint)
                car.rank = int(c.get("rank") or car.rank)
                car.finished = bool(c.get("finished") or False)

