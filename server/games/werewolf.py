"""
狼人杀游戏逻辑（简化版服务器权威）
"""
from __future__ import annotations

import random
from typing import Dict, Any, Optional, List

from .base import GameLogic, GameResult
from ..models.room import Room


class WerewolfGame(GameLogic):
    """简化版狼人杀：支持夜晚击杀、白天投票，直到一方灭绝"""

    GAME_TYPE = "werewolf"

    ROLES_POOL = [
        "werewolf",  # 狼人
        "villager",  # 村民
        "seer",      # 预言家
    ]

    def __init__(self, room: Room):
        super().__init__(room)
        self.players: Dict[str, Dict[str, Any]] = {}
        self.day_count: int = 0
        self.phase: str = "waiting"  # waiting / night / day / vote / over
        self.votes: Dict[str, str] = {}  # voter -> target
        self.last_kill: Optional[str] = None
        self.last_check: Optional[Dict[str, Any]] = None

    def init_game(self) -> Dict[str, Any]:
        self._assign_roles()
        self.day_count = 0
        self.phase = "night"
        self.is_finished = False
        self.winner = None
        self.votes.clear()
        self.last_kill = None
        self.last_check = None

        return {
            "type": "game_start",
            "game_type": self.GAME_TYPE,
            "phase": self.phase,
            "players": self._public_players(),
            "day": self.day_count,
        }

    def process_action(self, user_id: str, action: str, data: Dict[str, Any]) -> tuple:
        player = self.players.get(user_id)
        if not player or not player["alive"] or self.is_finished:
            return False, {"error": "无效玩家或游戏已结束"}, None

        # 夜晚：狼人击杀
        if self.phase == "night" and action == "wolf_kill":
            target = data.get("target")
            if player["role"] != "werewolf":
                return False, {"error": "你不是狼人"}, None
            if not self._is_alive(target):
                return False, {"error": "目标已死亡"}, None
            self.last_kill = target
            return True, {"success": True}, None

        # 夜晚：预言家查验
        if self.phase == "night" and action == "seer_check":
            target = data.get("target")
            if player["role"] != "seer":
                return False, {"error": "你不是预言家"}, None
            if not self._is_alive(target):
                return False, {"error": "目标已死亡"}, None
            role = self.players[target]["role"]
            self.last_check = {"target": target, "is_wolf": role == "werewolf"}
            return True, {"success": True}, None

        # 白天投票
        if self.phase == "vote" and action == "vote":
            target = data.get("target")
            if not self._is_alive(target):
                return False, {"error": "目标已死亡"}, None
            self.votes[user_id] = target
            return True, {"success": True}, None

        return False, {"error": "当前阶段无法执行该操作"}, None

    def update(self, dt: float):
        """阶段驱动：夜晚 -> 白天 -> 投票 -> 结算"""
        if self.is_finished:
            return

        if self.phase == "night":
            self._resolve_night()
        elif self.phase == "day":
            # 白天结束自动进入投票
            self.phase = "vote"
        elif self.phase == "vote":
            self._resolve_vote()

        self._check_win()

    def get_state(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "day": self.day_count,
            "players": self._public_players(),
            "last_kill": self.last_kill,
            "last_check": self.last_check,
            "votes": self.votes,
            "frame_id": self.frame_id,
        }

    def check_game_over(self) -> Optional[GameResult]:
        if not self.is_finished:
            return None
        scores = {pid: (100 if data["alive"] else 0) for pid, data in self.players.items()}
        return GameResult(
            winner_id=self.winner,
            scores=scores,
            stats={
                "day": self.day_count,
                "phase": self.phase,
                "players": self._public_players(include_role=True),
            },
        )

    def handle_disconnect(self, user_id: str) -> Dict[str, Any]:
        if self._is_alive(user_id):
            self.players[user_id]["alive"] = False
            self._check_win()
        return {"disconnected": user_id}

    # ========== 内部辅助 ==========
    def _assign_roles(self):
        player_ids = [p.user_id for p in self.room.players]
        roles = self._generate_roles(len(player_ids))
        self.players.clear()
        for uid, role in zip(player_ids, roles):
            self.players[uid] = {
                "user_id": uid,
                "role": role,
                "alive": True,
            }

    def _generate_roles(self, n: int) -> List[str]:
        roles: List[str] = []
        # 至少 1 狼 1 预言家，其余村民
        if n >= 2:
            roles.append("werewolf")
            roles.append("seer")
        while len(roles) < n:
            roles.append("villager")
        random.shuffle(roles)
        return roles

    def _is_alive(self, user_id: Optional[str]) -> bool:
        return bool(user_id) and user_id in self.players and self.players[user_id]["alive"]

    def _resolve_night(self):
        # 处理夜晚结果
        if self.last_kill and self._is_alive(self.last_kill):
            self.players[self.last_kill]["alive"] = False
        self.day_count += 1
        self.phase = "day"
        self.votes.clear()

    def _resolve_vote(self):
        if not self.votes:
            self.phase = "night"
            self.last_kill = None
            self.last_check = None
            return
        tally: Dict[str, int] = {}
        for target in self.votes.values():
            tally[target] = tally.get(target, 0) + 1
        # 最高票淘汰
        target = max(tally.items(), key=lambda x: x[1])[0]
        if self._is_alive(target):
            self.players[target]["alive"] = False
        self.phase = "night"
        self.last_kill = None
        self.last_check = None
        self.votes.clear()

    def _check_win(self):
        wolves = [p for p in self.players.values() if p["alive"] and p["role"] == "werewolf"]
        villagers = [p for p in self.players.values() if p["alive"] and p["role"] != "werewolf"]
        if not wolves:
            self.is_finished = True
            self.winner = next(iter(villagers), {}).get("user_id") if villagers else None
            self.phase = "over"
        elif len(wolves) >= len(villagers):
            self.is_finished = True
            self.winner = wolves[0]["user_id"] if wolves else None
            self.phase = "over"

    def _public_players(self, include_role: bool = False):
        data = []
        for p in self.players.values():
            entry = {
                "user_id": p["user_id"],
                "alive": p["alive"],
            }
            if include_role:
                entry["role"] = p["role"]
            data.append(entry)
        return data

