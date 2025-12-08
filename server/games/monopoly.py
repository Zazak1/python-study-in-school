"""
大富翁游戏逻辑（简化版服务器权威）
"""
from __future__ import annotations

import random
from typing import Dict, Any, Optional, List

from .base import GameLogic, GameResult
from ..models.room import Room


class MonopolyGame(GameLogic):
    """简化版大富翁：掷骰子→移动→可买地/付租金，破产淘汰"""

    GAME_TYPE = "monopoly"
    START_BONUS = 2000

    DEFAULT_MAP: List[Dict[str, Any]] = [
        {"type": "start", "name": "起点"},
        {"type": "property", "name": "地中海大道", "price": 600, "rent": [20, 100, 300, 900, 1600]},
        {"type": "chest", "name": "宝箱"},
        {"type": "property", "name": "波罗的海大道", "price": 600, "rent": [40, 200, 600, 1800, 3200]},
        {"type": "tax", "name": "所得税", "amount": 200},
        {"type": "station", "name": "火车站", "price": 2000, "rent": [250, 500, 1000, 2000]},
        {"type": "property", "name": "东方大道", "price": 1000, "rent": [60, 300, 900, 2700, 4000]},
        {"type": "chance", "name": "机会"},
        {"type": "property", "name": "佛蒙特大道", "price": 1000, "rent": [60, 300, 900, 2700, 4000]},
        {"type": "property", "name": "康涅狄格大道", "price": 1200, "rent": [80, 400, 1000, 3000, 4500]},
    ]

    def __init__(self, room: Room):
        super().__init__(room)
        self.players: Dict[str, Dict[str, Any]] = {}
        self.tiles: List[Dict[str, Any]] = []
        self.current_player: Optional[str] = None
        self.phase: str = "waiting"  # waiting / rolling / action / end

    def init_game(self) -> Dict[str, Any]:
        self._init_tiles()
        self._init_players()
        self.phase = "rolling"
        self.current_player = self.room.players[0].user_id if self.room.players else None
        self.is_finished = False
        self.winner = None

        return {
            "type": "game_start",
            "game_type": self.GAME_TYPE,
            "phase": self.phase,
            "current_player": self.current_player,
            "players": self._serialize_players(),
            "tiles": self._serialize_tiles(),
        }

    def process_action(self, user_id: str, action: str, data: Dict[str, Any]) -> tuple:
        if self.is_finished or user_id != self.current_player:
            return False, {"error": "未到你的回合"}, None
        player = self.players.get(user_id)
        if not player or player["bankrupt"]:
            return False, {"error": "玩家无效"}, None

        if action == "roll_dice" and self.phase == "rolling":
            d1, d2 = random.randint(1, 6), random.randint(1, 6)
            steps = d1 + d2
            passed_start = self._move_player(player, steps)
            msg = {
                "type": "game_action",
                "action": "player_move",
                "user_id": user_id,
                "position": player["position"],
                "dice": (d1, d2),
                "passed_start": passed_start,
                "players": self._serialize_players(),
            }
            self.phase = "action"
            # 处理落点效果（税、租金）
            follow = self._handle_tile(player)
            if follow:
                msg.update(follow)
            self._check_bankrupt()
            self._check_win()
            return True, {"success": True}, msg

        if action == "buy_property" and self.phase == "action":
            tile = self._get_tile(player["position"])
            if not tile or tile["type"] != "property":
                return False, {"error": "当前位置不可购买"}, None
            if tile.get("owner"):
                return False, {"error": "已被购买"}, None
            price = tile.get("price", 0)
            if player["money"] < price:
                return False, {"error": "余额不足"}, None
            player["money"] -= price
            tile["owner"] = user_id
            msg = {
                "type": "game_action",
                "action": "buy_property",
                "user_id": user_id,
                "tile_id": tile["id"],
                "money": player["money"],
            }
            self.phase = "end_turn"
            return True, {"success": True}, msg

        if action == "end_turn" and self.phase in ("action", "end_turn"):
            self._next_player()
            return True, {"success": True}, {
                "type": "game_action",
                "action": "turn_end",
                "next_player": self.current_player,
                "phase": self.phase,
            }

        return False, {"error": "无效操作或阶段"}, None

    def update(self, dt: float):
        # 回合制，无需帧更新
        pass

    def get_state(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "current_player": self.current_player,
            "players": self._serialize_players(),
            "tiles": self._serialize_tiles(),
            "frame_id": self.frame_id,
        }

    def check_game_over(self) -> Optional[GameResult]:
        if not self.is_finished:
            return None
        scores = {pid: data["money"] for pid, data in self.players.items()}
        return GameResult(
            winner_id=self.winner,
            scores=scores,
            stats={"tiles": self._serialize_tiles(), "players": self._serialize_players()},
        )

    # ========== 内部方法 ==========
    def _init_tiles(self):
        self.tiles = []
        for idx, tile in enumerate(self.DEFAULT_MAP):
            t = dict(tile)
            t["id"] = idx
            t["owner"] = None
            t.setdefault("rent", [])
            self.tiles.append(t)

    def _init_players(self):
        self.players.clear()
        for p in self.room.players:
            self.players[p.user_id] = {
                "user_id": p.user_id,
                "nickname": p.nickname,
                "position": 0,
                "money": 15000,
                "properties": [],
                "bankrupt": False,
            }

    def _move_player(self, player: Dict[str, Any], steps: int) -> bool:
        old = player["position"]
        new_pos = (old + steps) % len(self.tiles)
        passed_start = new_pos < old
        player["position"] = new_pos
        if passed_start:
            player["money"] += self.START_BONUS
        return passed_start

    def _handle_tile(self, player: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tile = self._get_tile(player["position"])
        if not tile:
            return None
        ttype = tile["type"]
        if ttype == "tax":
            amount = tile.get("amount", 0)
            player["money"] = max(0, player["money"] - amount)
            return {"tax": amount, "money": player["money"]}
        if ttype == "property" and tile.get("owner") and tile["owner"] != player["user_id"]:
            rent = tile.get("rent", [0])
            pay = rent[0] if rent else 0
            player["money"] = max(0, player["money"] - pay)
            owner = self.players.get(tile["owner"])
            if owner:
                owner["money"] += pay
            return {"pay_rent": {"to": tile["owner"], "amount": pay}, "money": player["money"]}
        return None

    def _next_player(self):
        alive_ids = [pid for pid, p in self.players.items() if not p["bankrupt"]]
        if not alive_ids:
            self.is_finished = True
            self.winner = None
            return
        if self.current_player not in alive_ids:
            current_idx = 0
        else:
            current_idx = alive_ids.index(self.current_player)
            current_idx = (current_idx + 1) % len(alive_ids)
        self.current_player = alive_ids[current_idx]
        self.phase = "rolling"

    def _check_bankrupt(self):
        for p in self.players.values():
            if p["money"] <= 0 and not p["bankrupt"]:
                p["bankrupt"] = True
                p["properties"].clear()
                # 释放地产
                for tile in self.tiles:
                    if tile.get("owner") == p["user_id"]:
                        tile["owner"] = None

    def _check_win(self):
        alive = [pid for pid, p in self.players.items() if not p["bankrupt"]]
        if len(alive) == 1:
            self.is_finished = True
            self.winner = alive[0]
            self.phase = "end"

    def _get_tile(self, tile_id: int) -> Optional[Dict[str, Any]]:
        if 0 <= tile_id < len(self.tiles):
            return self.tiles[tile_id]
        return None

    def _serialize_players(self):
        return [
            {
                "user_id": p["user_id"],
                "position": p["position"],
                "money": p["money"],
                "bankrupt": p["bankrupt"],
                "properties": p["properties"],
            }
            for p in self.players.values()
        ]

    def _serialize_tiles(self):
        return [
            {
                "id": t["id"],
                "type": t["type"],
                "name": t["name"],
                "owner": t.get("owner"),
                "price": t.get("price", 0),
                "rent": t.get("rent", []),
            }
            for t in self.tiles
        ]

