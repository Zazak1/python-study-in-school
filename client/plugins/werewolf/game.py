"""
狼人杀游戏插件（客户端，MVP）

权威规则在服务器端 `server/games/werewolf.py`。
客户端负责：
- 展示阶段/倒计时/玩家存活
- 发送 wolf_kill / seer_check / vote 等行动
- 接收私有信息（角色、查验结果等）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..base import EventType, GameContext, GamePlugin, GameState, NetworkEvent, RoomState


@dataclass
class PlayerState:
    user_id: str
    alive: bool = True


class WerewolfPlugin(GamePlugin):
    PLUGIN_NAME = "werewolf"
    PLUGIN_VERSION = "0.1.0"
    PLUGIN_DESCRIPTION = "狼人杀（MVP：服务器权威阶段驱动）"
    MIN_PLAYERS = 6
    MAX_PLAYERS = 12
    SUPPORTS_SPECTATE = True

    def __init__(self):
        super().__init__()
        self._players: Dict[str, PlayerState] = {}
        self._phase: str = "waiting"  # night/day/vote/over
        self._day: int = 0
        self._timer: float = 0.0

        self._my_user_id: str = ""
        self._my_role: Optional[str] = None  # werewolf/seer/villager
        self._seer_result: Optional[Dict[str, Any]] = None

    def load(self, context: GameContext) -> bool:
        self._context = context
        self._state = GameState.LOADING

        if context.local_user:
            self._my_user_id = context.local_user.user_id

        self._players.clear()
        self._phase = "waiting"
        self._day = 0
        self._timer = 0.0
        self._my_role = None
        self._seer_result = None

        self._state = GameState.READY
        self._is_loaded = True
        return True

    def join_room(self, room_state: RoomState) -> bool:
        self._room_state = room_state
        for p in room_state.current_players:
            self._players.setdefault(p.user_id, PlayerState(user_id=p.user_id, alive=True))
        return True

    def start_game(self) -> bool:
        self._state = GameState.PLAYING
        return True

    def dispose(self) -> None:
        self._players.clear()
        self._phase = "waiting"
        self._day = 0
        self._timer = 0.0
        self._my_role = None
        self._seer_result = None
        self._state = GameState.IDLE
        self._is_loaded = False

    def update(self, dt: float) -> None:
        return

    def render(self, surface: Any) -> Dict[str, Any]:
        return {
            "phase": self._phase,
            "day": self._day,
            "timer": self._timer,
            "my_role": self._my_role,
            "seer_result": self._seer_result,
            "players": {uid: {"alive": p.alive} for uid, p in self._players.items()},
            "alive_players": [uid for uid, p in self._players.items() if p.alive],
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

        if event.type == EventType.SYSTEM:
            payload = event.payload or {}
            action = payload.get("action")
            if action == "role":
                role = payload.get("role")
                self._my_role = str(role) if role else None
            elif action == "seer_result":
                self._seer_result = {
                    "target": payload.get("target"),
                    "is_wolf": bool(payload.get("is_wolf")),
                }
            return

    # ========== 发送操作 ==========
    def can_act(self) -> bool:
        if self._state != GameState.PLAYING:
            return False
        if not self._my_role:
            return False
        if self._phase == "night":
            return self._my_role in {"werewolf", "seer"}
        if self._phase == "vote":
            return True
        return False

    def wolf_kill(self, target_id: str):
        if self._my_role != "werewolf" or self._phase != "night":
            return
        self.send_input({"action": "wolf_kill", "target": target_id})

    def seer_check(self, target_id: str):
        if self._my_role != "seer" or self._phase != "night":
            return
        self.send_input({"action": "seer_check", "target": target_id})

    def vote(self, target_id: str):
        if self._phase != "vote":
            return
        self.send_input({"action": "vote", "target": target_id})

    # ========== 内部 ==========
    def _apply_state(self, state: Dict[str, Any]):
        self._phase = str(state.get("phase") or self._phase)
        self._day = int(state.get("day") or self._day)
        timer = state.get("timer")
        if timer is not None:
            try:
                self._timer = float(timer)
            except Exception:
                pass

        players = state.get("players")
        if isinstance(players, list):
            for p in players:
                if not isinstance(p, dict):
                    continue
                uid = p.get("user_id")
                if not uid:
                    continue
                uid = str(uid)
                alive = bool(p.get("alive", True))
                self._players[uid] = PlayerState(user_id=uid, alive=alive)

