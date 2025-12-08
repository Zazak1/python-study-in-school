"""
2D 射击游戏逻辑（服务器权威）
"""
from __future__ import annotations

import math
import uuid
from typing import Dict, Any, Optional, Tuple

from .base import GameLogic, GameResult
from ..models.room import Room


class Shooter2DGame(GameLogic):
    """2D 射击游戏（帧同步）"""

    GAME_TYPE = "shooter2d"

    # 地图与物理参数（需与客户端保持一致）
    MAP_WIDTH = 1920
    MAP_HEIGHT = 1080
    PLAYER_SPEED = 200.0
    BULLET_SPEED = 500.0
    PLAYER_RADIUS = 18.0
    BULLET_RADIUS = 6.0
    MAX_HEALTH = 100

    def __init__(self, room: Room):
        super().__init__(room)
        self.players: Dict[str, Dict[str, Any]] = {}
        self.bullets: Dict[str, Dict[str, Any]] = {}
        self.pending_inputs: Dict[str, Tuple[float, float]] = {}  # user_id -> (dx, dy)
        self.winner_team: Optional[int] = None

    def init_game(self) -> Dict[str, Any]:
        """初始化游戏"""
        self._spawn_players()
        self.is_finished = False
        self.winner = None
        self.winner_team = None

        return {
            "type": "game_start",
            "game_type": self.GAME_TYPE,
            "players": self._serialize_players(),
            "bullets": [],
            "map": {"width": self.MAP_WIDTH, "height": self.MAP_HEIGHT},
            "frame_id": self.frame_id,
        }

    def process_action(self, user_id: str, action: str, data: Dict[str, Any]) -> tuple:
        """处理玩家输入"""
        player = self.players.get(user_id)
        if not player or not player["is_alive"]:
            return False, {"error": "玩家不存在或已阵亡"}, None

        if action == "move":
            dx = float(data.get("dx", 0))
            dy = float(data.get("dy", 0))
            # 输入归一化
            length = math.hypot(dx, dy)
            if length > 0:
                dx /= length
                dy /= length
            self.pending_inputs[user_id] = (dx, dy)
            return True, {"success": True}, None

        if action == "fire":
            # 客户端提供射击方向，服务器只做权威生成
            dir_x = float(data.get("dx", 0))
            dir_y = float(data.get("dy", 0))
            length = math.hypot(dir_x, dir_y)
            if length == 0:
                return False, {"error": "无效方向"}, None
            dir_x /= length
            dir_y /= length

            bullet_id = str(uuid.uuid4())[:12]
            bullet = {
                "id": bullet_id,
                "owner_id": user_id,
                "x": player["x"],
                "y": player["y"],
                "vx": dir_x * self.BULLET_SPEED,
                "vy": dir_y * self.BULLET_SPEED,
                "damage": 10,
                "is_active": True,
            }
            self.bullets[bullet_id] = bullet

            # 即时广播开火事件，减少感知延迟
            broadcast = {
                "type": "game_action",
                "action": "fire",
                "bullet": bullet,
                "frame_id": self.frame_id,
            }
            return True, {"success": True}, broadcast

        return False, {"error": "未知操作"}, None

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态（用于帧同步/重连）"""
        return {
            "players": self._serialize_players(),
            "bullets": self._serialize_bullets(),
            "frame_id": self.frame_id,
        }

    def check_game_over(self) -> Optional[GameResult]:
        """检测游戏结束"""
        if not self.is_finished:
            return None

        scores = {pid: (100 if data["is_alive"] else 0) for pid, data in self.players.items()}
        return GameResult(
            winner_id=self.winner,
            scores=scores,
            stats={
                "frame_id": self.frame_id,
                "players": self._serialize_players(),
                "bullets": len(self.bullets),
                "winner_team": self.winner_team,
            },
        )

    def update(self, dt: float):
        """帧更新：移动、子弹、碰撞"""
        if self.is_finished:
            return

        self._apply_player_inputs(dt)
        self._update_bullets(dt)
        self._check_game_over()

    def handle_disconnect(self, user_id: str) -> Dict[str, Any]:
        """断线视为阵亡"""
        player = self.players.get(user_id)
        if player and player["is_alive"]:
            player["is_alive"] = False
            player["health"] = 0
            self._check_game_over()

        return {"disconnected": user_id}

    # ========== 内部方法 ==========

    def _spawn_players(self):
        """分配初始位置与队伍"""
        self.players.clear()
        self.bullets.clear()
        self.pending_inputs.clear()

        count = max(len(self.room.players), 1)
        # 简单分布：沿圆周均匀分布
        radius = min(self.MAP_WIDTH, self.MAP_HEIGHT) * 0.35
        cx, cy = self.MAP_WIDTH / 2, self.MAP_HEIGHT / 2

        for idx, room_player in enumerate(self.room.players):
            angle = 2 * math.pi * idx / count
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            team = idx % 2  # 简单双队伍

            self.players[room_player.user_id] = {
                "user_id": room_player.user_id,
                "nickname": room_player.nickname,
                "x": x,
                "y": y,
                "vx": 0.0,
                "vy": 0.0,
                "rotation": angle,
                "health": self.MAX_HEALTH,
                "is_alive": True,
                "team": team,
            }

    def _apply_player_inputs(self, dt: float):
        """应用移动输入"""
        for user_id, player in self.players.items():
            if not player["is_alive"]:
                continue
            dx, dy = self.pending_inputs.get(user_id, (0.0, 0.0))

            player["x"] += dx * self.PLAYER_SPEED * dt
            player["y"] += dy * self.PLAYER_SPEED * dt

            # 边界限制
            player["x"] = max(0, min(self.MAP_WIDTH, player["x"]))
            player["y"] = max(0, min(self.MAP_HEIGHT, player["y"]))

        # 输入只生效一帧，需持续发送
        self.pending_inputs.clear()

    def _update_bullets(self, dt: float):
        """更新子弹并检查碰撞"""
        to_remove = []
        for bullet_id, bullet in self.bullets.items():
            if not bullet["is_active"]:
                to_remove.append(bullet_id)
                continue

            bullet["x"] += bullet["vx"] * dt
            bullet["y"] += bullet["vy"] * dt

            # 越界移除
            if (
                bullet["x"] < 0
                or bullet["x"] > self.MAP_WIDTH
                or bullet["y"] < 0
                or bullet["y"] > self.MAP_HEIGHT
            ):
                to_remove.append(bullet_id)
                continue

            # 简单圆形碰撞检测
            for player_id, player in self.players.items():
                if not player["is_alive"] or player_id == bullet["owner_id"]:
                    continue
                if self._check_collision(
                    (bullet["x"], bullet["y"]),
                    (player["x"], player["y"]),
                    self.BULLET_RADIUS + self.PLAYER_RADIUS,
                ):
                    player["health"] -= bullet["damage"]
                    if player["health"] <= 0:
                        player["is_alive"] = False
                        player["health"] = 0
                    to_remove.append(bullet_id)
                    break

        for bid in to_remove:
            self.bullets.pop(bid, None)

    def _check_collision(self, a: Tuple[float, float], b: Tuple[float, float], radius: float) -> bool:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return dx * dx + dy * dy <= radius * radius

    def _check_game_over(self):
        """检查剩余存活队伍"""
        alive_players = [p for p in self.players.values() if p["is_alive"]]
        if not alive_players:
            self.is_finished = True
            self.winner = None
            self.winner_team = None
            return

        teams_alive = {p["team"] for p in alive_players}
        if len(teams_alive) == 1:
            self.is_finished = True
            self.winner_team = teams_alive.pop()
            # 任意存活玩家作为胜者代表
            self.winner = alive_players[0]["user_id"]

    def _serialize_players(self):
        return [
            {
                "user_id": p["user_id"],
                "nickname": p["nickname"],
                "x": p["x"],
                "y": p["y"],
                "rotation": p["rotation"],
                "health": p["health"],
                "is_alive": p["is_alive"],
                "team": p["team"],
            }
            for p in self.players.values()
        ]

    def _serialize_bullets(self):
        return [
            {
                "id": b["id"],
                "owner_id": b["owner_id"],
                "x": b["x"],
                "y": b["y"],
                "vx": b["vx"],
                "vy": b["vy"],
                "damage": b["damage"],
            }
            for b in self.bullets.values()
        ]

