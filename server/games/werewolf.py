"""
狼人杀游戏逻辑（服务器权威，MVP）

特点：
- 阶段驱动（night -> day -> vote -> night ...）
- tick_rate 建议为 1Hz（按秒倒计时）
- 身份牌通过 GameService 的私有初始化数据单发（避免泄露）
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from .base import GameLogic, GameResult
from ..models.room import Room


class WerewolfGame(GameLogic):
    """简化版狼人杀：夜晚击杀 + 预言家查验 + 白天投票"""

    GAME_TYPE = "werewolf"

    PHASES = ("night", "day", "vote", "over")

    # MVP：固定时长（秒）
    NIGHT_SECONDS = 20.0
    DAY_SECONDS = 20.0
    VOTE_SECONDS = 15.0

    def __init__(self, room: Room):
        super().__init__(room)
        # players: user_id -> {role, alive}
        self.players: Dict[str, Dict[str, Any]] = {}
        self.day_count: int = 0
        self.phase: str = "waiting"
        self.timer: float = 0.0

        # 夜晚行动
        self.last_kill: Optional[str] = None
        # 狼人击杀投票：wolf_id -> target_id
        self.wolf_votes: Dict[str, str] = {}
        # 预言家每夜只允许查验一次：seer_id 集合
        self.seer_used: set[str] = set()
        # votes: voter -> target
        self.votes: Dict[str, str] = {}

    def init_game(self) -> Dict[str, Any]:
        self._assign_roles()
        self.day_count = 0
        self.phase = "night"
        self.timer = self.NIGHT_SECONDS
        self.is_finished = False
        self.winner = None
        self.votes.clear()
        self.last_kill = None
        self.wolf_votes.clear()
        self.seer_used.clear()

        return {
            "type": "game_start",
            "game_type": self.GAME_TYPE,
            "phase": self.phase,
            "timer": self.timer,
            "day": self.day_count,
            "players": self._public_players(),
        }

    def get_private_init(self, user_id: str) -> Optional[Dict[str, Any]]:
        if user_id not in self.players:
            return None
        wolves = [uid for uid, p in self.players.items() if p.get("role") == "werewolf"]
        return {
            "type": "game_private",
            "game_type": self.GAME_TYPE,
            "action": "role",
            "role": self.players[user_id]["role"],
            # 仅狼人可见同伴列表（MVP：方便 UI 展示/协作）
            "wolves": wolves if self.players[user_id]["role"] == "werewolf" else [],
        }

    def process_action(self, user_id: str, action: str, data: Dict[str, Any]) -> tuple:
        player = self.players.get(user_id)
        if not player or not player["alive"] or self.is_finished:
            return False, {"error": "无效玩家或游戏已结束"}, None

        if self.phase == "night" and action == "wolf_kill":
            if player["role"] != "werewolf":
                return False, {"error": "你不是狼人"}, None
            target = data.get("target")
            if not self._is_alive(target):
                return False, {"error": "目标已死亡"}, None
            self.wolf_votes[user_id] = str(target)
            return True, {"success": True}, None

        if self.phase == "night" and action == "seer_check":
            if player["role"] != "seer":
                return False, {"error": "你不是预言家"}, None
            if user_id in self.seer_used:
                return False, {"error": "本回合已查验"}, None
            target = data.get("target")
            if not self._is_alive(target):
                return False, {"error": "目标已死亡"}, None
            self.seer_used.add(user_id)
            role = self.players[str(target)]["role"]
            # 私有结果通过 game_action_response 回给发起者（不广播）
            return True, {"action": "seer_result", "target": str(target), "is_wolf": role == "werewolf"}, None

        if self.phase == "vote" and action == "vote":
            target = data.get("target")
            if not self._is_alive(target):
                return False, {"error": "目标已死亡"}, None
            self.votes[user_id] = str(target)
            return True, {"success": True}, None

        return False, {"error": "当前阶段无法执行该操作"}, None

    def update(self, dt: float):
        """按倒计时推进阶段；投票可在全员投完时提前结束。"""
        if self.is_finished or self.phase == "over":
            return

        self.timer = max(0.0, self.timer - dt)

        # 提前结束：投票阶段全员投完
        if self.phase == "vote":
            alive_ids = self._alive_ids()
            if alive_ids and all(uid in self.votes for uid in alive_ids):
                self.timer = 0.0

        if self.timer > 0.0:
            return

        if self.phase == "night":
            self._resolve_night()
            self._check_win()
            if self.is_finished:
                return
            self.phase = "day"
            self.timer = self.DAY_SECONDS
            return

        if self.phase == "day":
            self.phase = "vote"
            self.timer = self.VOTE_SECONDS
            self.votes.clear()
            return

        if self.phase == "vote":
            self._resolve_vote()
            self._check_win()
            if self.is_finished:
                return
            self.phase = "night"
            self.timer = self.NIGHT_SECONDS
            self.last_kill = None
            self.votes.clear()
            self.wolf_votes.clear()
            self.seer_used.clear()
            return

    def get_state(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "day": self.day_count,
            "timer": self.timer,
            "players": self._public_players(),
            "last_kill": self.last_kill,
            # votes 对外只用于 UI（MVP）；正式版应只在结算后公布
            "votes": dict(self.votes),
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

    # ========== 内部 ==========
    def _assign_roles(self):
        player_ids = [p.user_id for p in self.room.players]
        roles = self._generate_roles(len(player_ids))
        self.players.clear()
        for uid, role in zip(player_ids, roles):
            self.players[uid] = {"user_id": uid, "role": role, "alive": True}

    def _generate_roles(self, n: int) -> List[str]:
        roles: List[str] = []
        # 简化分配：约 1/3 狼人 + 1 预言家，其余村民
        if n <= 0:
            return roles
        wolves = max(1, n // 3)
        roles.extend(["werewolf"] * wolves)
        if n >= 2:
            roles.append("seer")
        while len(roles) < n:
            roles.append("villager")
        random.shuffle(roles)
        return roles

    def _is_alive(self, user_id: Optional[str]) -> bool:
        return bool(user_id) and str(user_id) in self.players and self.players[str(user_id)]["alive"]

    def _alive_ids(self) -> List[str]:
        return [uid for uid, p in self.players.items() if p["alive"]]

    def _resolve_night(self):
        # 选择击杀目标：狼人投票多数决；平票随机
        self.last_kill = None
        alive_wolves = [uid for uid, p in self.players.items() if p["alive"] and p["role"] == "werewolf"]
        votes = {wolf: target for wolf, target in self.wolf_votes.items() if wolf in alive_wolves}
        if votes:
            tally: Dict[str, int] = {}
            for target in votes.values():
                tally[target] = tally.get(target, 0) + 1
            if tally:
                max_count = max(tally.values())
                candidates = [t for t, c in tally.items() if c == max_count]
                self.last_kill = random.choice(candidates) if candidates else None

        if self.last_kill and self._is_alive(self.last_kill):
            self.players[self.last_kill]["alive"] = False
        self.day_count += 1

    def _resolve_vote(self):
        if not self.votes:
            return
        tally: Dict[str, int] = {}
        for target in self.votes.values():
            tally[target] = tally.get(target, 0) + 1
        max_count = max(tally.values()) if tally else 0
        candidates = [t for t, c in tally.items() if c == max_count] if max_count else []
        target = random.choice(candidates) if candidates else None
        if self._is_alive(target):
            self.players[str(target)]["alive"] = False

    def _check_win(self):
        wolves = [p for p in self.players.values() if p["alive"] and p["role"] == "werewolf"]
        villagers = [p for p in self.players.values() if p["alive"] and p["role"] != "werewolf"]

        if not wolves:
            self.is_finished = True
            self.winner = villagers[0]["user_id"] if villagers else None
            self.phase = "over"
            self.timer = 0.0
            return

        if len(wolves) >= len(villagers):
            self.is_finished = True
            self.winner = wolves[0]["user_id"] if wolves else None
            self.phase = "over"
            self.timer = 0.0

    def _public_players(self, include_role: bool = False):
        data = []
        for p in self.players.values():
            entry = {"user_id": p["user_id"], "alive": p["alive"]}
            if include_role:
                entry["role"] = p["role"]
            data.append(entry)
        return data
