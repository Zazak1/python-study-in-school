"""
赛车竞速游戏逻辑（简化版服务器权威）
"""
from __future__ import annotations

import math
from typing import Dict, Any, Optional, List, Tuple

from .base import GameLogic, GameResult
from ..models.room import Room


class RacingGame(GameLogic):
    """简化赛车：权威更新车辆物理，按圈数/检查点判断完赛"""

    GAME_TYPE = "racing"

    MAX_SPEED = 200.0
    ACCELERATION = 50.0
    BRAKE_FORCE = 80.0
    TURN_SPEED = 2.5
    DRAG = 0.02

    def __init__(self, room: Room):
        super().__init__(room)
        self.cars: Dict[str, Dict[str, Any]] = {}
        self.track: Dict[str, Any] = {}
        self.state: str = "waiting"  # waiting / countdown / racing / finished
        self.race_time: float = 0.0
        self.countdown: int = 3
        self.total_laps: int = 3

    def init_game(self) -> Dict[str, Any]:
        self._load_track()
        self._spawn_cars()
        self.state = "countdown"
        self.countdown = 3
        self.race_time = 0.0
        self.is_finished = False
        self.winner = None

        return {
            "type": "game_start",
            "game_type": self.GAME_TYPE,
            "state": self.state,
            "countdown": self.countdown,
            "cars": self._serialize_cars(),
            "track": self.track,
        }

    def process_action(self, user_id: str, action: str, data: Dict[str, Any]) -> tuple:
        car = self.cars.get(user_id)
        if not car or self.state not in ("countdown", "racing"):
            return False, {"error": "无法接受输入"}, None

        if action == "game_input":
            car["throttle"] = max(0.0, min(1.0, float(data.get("throttle", 0))))
            car["brake"] = max(0.0, min(1.0, float(data.get("brake", 0))))
            car["steering"] = max(-1.0, min(1.0, float(data.get("steering", 0))))
            return True, {"success": True}, None

        return False, {"error": "未知操作"}, None

    def update(self, dt: float):
        if self.is_finished:
            return
        if self.state == "countdown":
            self.countdown -= 1 if dt >= 1 else 0
            if self.countdown <= 0:
                self.state = "racing"
            return

        if self.state != "racing":
            return

        self.race_time += dt
        for car in self.cars.values():
            if car["finished"]:
                continue
            self._update_car_physics(car, dt)
            self._check_checkpoint_and_lap(car)

        self._check_finish()

    def get_state(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "race_time": self.race_time,
            "countdown": self.countdown,
            "cars": self._serialize_cars(),
            "track": self.track,
            "frame_id": self.frame_id,
        }

    def check_game_over(self) -> Optional[GameResult]:
        if not self.is_finished:
            return None
        scores = {cid: (100 - car["rank"] * 10 if car["rank"] else 0) for cid, car in self.cars.items()}
        return GameResult(
            winner_id=self.winner,
            scores=scores,
            stats={"cars": self._serialize_cars(), "race_time": self.race_time},
        )

    def handle_disconnect(self, user_id: str) -> Dict[str, Any]:
        car = self.cars.get(user_id)
        if car:
            car["finished"] = True
            car["rank"] = len(self.cars)
        self._check_finish(force=True)
        return {"disconnected": user_id}

    # ========== 内部方法 ==========
    def _load_track(self):
        # 简化默认赛道
        self.track = {
            "name": "default",
            "total_laps": self.total_laps,
            "checkpoints": [
                (0, 0, 50),
                (50, 0, 50),
                (50, 0, 0),
                (0, 0, 0),
            ],
            "start_positions": [
                (0, 0, -5),
                (3, 0, -5),
                (-3, 0, -8),
                (0, 0, -8),
            ],
        }

    def _spawn_cars(self):
        self.cars.clear()
        starts = self.track["start_positions"]
        for idx, p in enumerate(self.room.players):
            sx, sy, sz = starts[idx % len(starts)]
            self.cars[p.user_id] = {
                "user_id": p.user_id,
                "nickname": p.nickname,
                "pos": {"x": sx, "y": sy, "z": sz},
                "vel": {"x": 0.0, "y": 0.0, "z": 0.0},
                "rotation": 0.0,
                "lap": 0,
                "checkpoint": 0,
                "rank": 0,
                "finished": False,
                "throttle": 0.0,
                "brake": 0.0,
                "steering": 0.0,
            }

    def _update_car_physics(self, car: Dict[str, Any], dt: float):
        vel = car["vel"]
        rot = car["rotation"]
        # 转向
        if math.hypot(vel["x"], vel["z"]) > 1e-3:
            rot += car["steering"] * self.TURN_SPEED * dt
        car["rotation"] = rot
        dir_x = math.sin(rot)
        dir_z = math.cos(rot)
        # 加速
        if car["throttle"] > 0:
            accel = self.ACCELERATION * car["throttle"] * dt
            vel["x"] += dir_x * accel
            vel["z"] += dir_z * accel
        # 刹车
        if car["brake"] > 0:
            brake = self.BRAKE_FORCE * car["brake"] * dt
            speed = math.hypot(vel["x"], vel["z"])
            if speed > brake:
                ratio = (speed - brake) / speed
                vel["x"] *= ratio
                vel["z"] *= ratio
            else:
                vel["x"], vel["z"] = 0.0, 0.0
        # 阻力
        vel["x"] *= (1 - self.DRAG)
        vel["z"] *= (1 - self.DRAG)
        # 限速
        speed = math.hypot(vel["x"], vel["z"])
        if speed > self.MAX_SPEED:
            ratio = self.MAX_SPEED / speed
            vel["x"] *= ratio
            vel["z"] *= ratio
        # 位置更新
        pos = car["pos"]
        pos["x"] += vel["x"] * dt
        pos["z"] += vel["z"] * dt

    def _check_checkpoint_and_lap(self, car: Dict[str, Any]):
        cps: List[Tuple[float, float, float]] = self.track["checkpoints"]
        cp_idx = car["checkpoint"] % len(cps)
        cp = cps[cp_idx]
        # 简化：距离检查点小于阈值视为通过
        if self._distance(car["pos"], cp) < 5.0:
            car["checkpoint"] += 1
            if car["checkpoint"] % len(cps) == 0:
                car["lap"] += 1

    def _check_finish(self, force: bool = False):
        # 完赛条件：所有车完成 total_laps 或全部离线
        finished = [c for c in self.cars.values() if c["finished"]]
        active = [c for c in self.cars.values() if not c["finished"]]
        for car in active:
            if car["lap"] >= self.total_laps:
                car["finished"] = True
                car["rank"] = len(finished) + 1
                finished.append(car)
        if force:
            for car in active:
                car["finished"] = True
                car["rank"] = len(finished) + 1
                finished.append(car)
        if len(finished) == len(self.cars):
            self.is_finished = True
            self.state = "finished"
            # 以 rank=1 为胜者
            winner = sorted(self.cars.values(), key=lambda c: (c["rank"] or 9999))[0]
            self.winner = winner["user_id"]

    def _distance(self, pos: Dict[str, float], cp: Tuple[float, float, float]) -> float:
        dx = pos["x"] - cp[0]
        dy = pos["y"] - cp[1]
        dz = pos["z"] - cp[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def _serialize_cars(self):
        return [
            {
                "user_id": c["user_id"],
                "nickname": c["nickname"],
                "pos": c["pos"],
                "vel": c["vel"],
                "rotation": c["rotation"],
                "lap": c["lap"],
                "checkpoint": c["checkpoint"],
                "rank": c["rank"],
                "finished": c["finished"],
            }
            for c in self.cars.values()
        ]

