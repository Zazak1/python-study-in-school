"""
赛车竞速游戏插件
"""
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import math

from ..base import GamePlugin


class RaceState(Enum):
    """比赛状态"""
    WAITING = auto()    # 等待
    COUNTDOWN = auto()  # 倒计时
    RACING = auto()     # 比赛中
    FINISHED = auto()   # 完成


@dataclass
class Vector3:
    """3D 向量"""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)


@dataclass
class CarState:
    """车辆状态"""
    user_id: str
    nickname: str
    
    # 物理状态
    position: Vector3 = field(default_factory=Vector3)
    velocity: Vector3 = field(default_factory=Vector3)
    rotation: float = 0.0  # 航向角（弧度）
    
    # 比赛状态
    lap: int = 0          # 当前圈数
    checkpoint: int = 0   # 当前检查点
    rank: int = 0         # 排名
    finish_time: float = 0.0  # 完成时间
    is_finished: bool = False
    
    # 输入
    throttle: float = 0.0  # 油门 [0, 1]
    brake: float = 0.0     # 刹车 [0, 1]
    steering: float = 0.0  # 转向 [-1, 1]


@dataclass
class TrackData:
    """赛道数据"""
    name: str
    total_laps: int = 3
    checkpoints: List[Tuple[float, float, float]] = field(default_factory=list)
    start_positions: List[Tuple[float, float, float]] = field(default_factory=list)


class RacingPlugin(GamePlugin):
    """赛车竞速游戏插件"""
    
    GAME_TYPE = "racing"
    NAME = "赛车竞速"
    VERSION = "0.1.0"
    
    # 物理参数
    MAX_SPEED = 200.0       # 最大速度 km/h
    ACCELERATION = 50.0     # 加速度
    BRAKE_FORCE = 80.0      # 刹车力度
    TURN_SPEED = 2.5        # 转向速度
    DRAG = 0.02             # 阻力
    
    def __init__(self):
        super().__init__()
        self.state = RaceState.WAITING
        self.cars: Dict[str, CarState] = {}
        self.track: Optional[TrackData] = None
        self.my_user_id: Optional[str] = None
        
        # 时间
        self.race_time: float = 0.0
        self.countdown: int = 0
        
        # 预测
        self.pending_inputs: List[Dict] = []
        self.last_server_frame: int = 0
        
        # 回调
        self.on_countdown = None
        self.on_race_start = None
        self.on_lap_complete = None
        self.on_race_finish = None
    
    def get_game_info(self) -> Dict[str, Any]:
        return {
            "game_type": self.GAME_TYPE,
            "name": self.NAME,
            "version": self.VERSION,
            "description": "3D 赛车竞速，支持多赛道和联机对战",
            "icon": "🏎️",
            "color": "#06B6D4",
            "min_players": 2,
            "max_players": 6,
            "features": ["多赛道", "漂移", "道具"]
        }
    
    def load(self, context: Dict[str, Any]):
        """加载游戏"""
        self._is_loaded = True
        self.my_user_id = context.get('user_id')
        
        # 加载赛道数据
        track_name = context.get('track', 'default')
        self._load_track(track_name)
    
    def _load_track(self, name: str):
        """加载赛道"""
        # 默认赛道
        self.track = TrackData(
            name=name,
            total_laps=3,
            checkpoints=[
                (0, 0, 100),
                (100, 0, 100),
                (100, 0, 0),
                (0, 0, 0),
            ],
            start_positions=[
                (0, 0, -10),
                (5, 0, -10),
                (-5, 0, -15),
                (0, 0, -15),
                (5, 0, -20),
                (-5, 0, -20),
            ]
        )
    
    def join_room(self, room_state: Dict[str, Any]):
        """加入房间"""
        self._room_id = room_state.get('room_id')
        
        # 初始化玩家车辆
        for i, p in enumerate(room_state.get('players', [])):
            start_pos = self.track.start_positions[i] if self.track else (0, 0, 0)
            
            self.cars[p['user_id']] = CarState(
                user_id=p['user_id'],
                nickname=p['nickname'],
                position=Vector3(*start_pos)
            )
    
    def on_network(self, event: Dict[str, Any]):
        """处理网络事件"""
        event_type = event.get('type')
        payload = event.get('payload', {})
        
        if event_type == 'countdown':
            self.state = RaceState.COUNTDOWN
            self.countdown = payload.get('count', 3)
            if self.on_countdown:
                self.on_countdown(self.countdown)
        
        elif event_type == 'race_start':
            self.state = RaceState.RACING
            self.race_time = 0
            if self.on_race_start:
                self.on_race_start()
        
        elif event_type == 'sync':
            # 服务器权威状态同步
            self._apply_server_state(payload)
        
        elif event_type == 'lap_complete':
            user_id = payload.get('user_id')
            lap = payload.get('lap')
            if user_id in self.cars:
                self.cars[user_id].lap = lap
            if self.on_lap_complete:
                self.on_lap_complete(user_id, lap)
        
        elif event_type == 'race_finish':
            user_id = payload.get('user_id')
            finish_time = payload.get('time')
            rank = payload.get('rank')
            
            if user_id in self.cars:
                car = self.cars[user_id]
                car.is_finished = True
                car.finish_time = finish_time
                car.rank = rank
            
            if self.on_race_finish:
                self.on_race_finish(user_id, rank, finish_time)
            
            # 检查是否所有人都完成
            if all(c.is_finished for c in self.cars.values()):
                self.state = RaceState.FINISHED
    
    def _apply_server_state(self, payload: Dict):
        """应用服务器状态"""
        frame = payload.get('frame', 0)
        self.last_server_frame = frame
        
        for car_data in payload.get('cars', []):
            user_id = car_data.get('user_id')
            if user_id in self.cars:
                car = self.cars[user_id]
                car.position = Vector3(**car_data.get('position', {}))
                car.velocity = Vector3(**car_data.get('velocity', {}))
                car.rotation = car_data.get('rotation', 0)
                car.lap = car_data.get('lap', 0)
                car.checkpoint = car_data.get('checkpoint', 0)
        
        # 清理已确认的输入
        self.pending_inputs = [
            inp for inp in self.pending_inputs 
            if inp.get('frame', 0) > frame
        ]
    
    def update(self, dt: float):
        """更新游戏"""
        if self.state != RaceState.RACING:
            return
        
        self.race_time += dt
        
        # 客户端预测自己的车辆
        my_car = self.cars.get(self.my_user_id)
        if my_car and not my_car.is_finished:
            self._update_car_physics(my_car, dt)
    
    def _update_car_physics(self, car: CarState, dt: float):
        """更新车辆物理（简化版）"""
        # 转向
        if abs(car.velocity.magnitude()) > 1:
            car.rotation += car.steering * self.TURN_SPEED * dt
        
        # 方向向量
        dir_x = math.sin(car.rotation)
        dir_z = math.cos(car.rotation)
        
        # 加速/刹车
        if car.throttle > 0:
            accel = self.ACCELERATION * car.throttle * dt
            car.velocity.x += dir_x * accel
            car.velocity.z += dir_z * accel
        
        if car.brake > 0:
            brake = self.BRAKE_FORCE * car.brake * dt
            speed = car.velocity.magnitude()
            if speed > brake:
                ratio = (speed - brake) / speed
                car.velocity.x *= ratio
                car.velocity.z *= ratio
            else:
                car.velocity = Vector3()
        
        # 阻力
        car.velocity.x *= (1 - self.DRAG)
        car.velocity.z *= (1 - self.DRAG)
        
        # 限速
        speed = car.velocity.magnitude()
        if speed > self.MAX_SPEED:
            ratio = self.MAX_SPEED / speed
            car.velocity.x *= ratio
            car.velocity.z *= ratio
        
        # 位置更新
        car.position = car.position + car.velocity * dt
    
    def render(self, surface):
        """渲染（由 3D 引擎处理）"""
        pass
    
    def dispose(self):
        """释放资源"""
        self._is_loaded = False
        self.cars.clear()
    
    # ========== 输入控制 ==========
    
    def set_input(self, throttle: float, brake: float, steering: float):
        """设置输入"""
        my_car = self.cars.get(self.my_user_id)
        if not my_car:
            return
        
        my_car.throttle = max(0, min(1, throttle))
        my_car.brake = max(0, min(1, brake))
        my_car.steering = max(-1, min(1, steering))
        
        # 发送输入到服务器
        self._send_input({
            'throttle': my_car.throttle,
            'brake': my_car.brake,
            'steering': my_car.steering
        })
    
    def _send_input(self, input_data: Dict):
        """发送输入"""
        if self._network_callback:
            self._network_callback({
                'type': 'game_input',
                'room_id': self._room_id,
                'input': input_data,
                'timestamp': self.race_time
            })
    
    # ========== 查询方法 ==========
    
    def get_my_car(self) -> Optional[CarState]:
        """获取我的车辆"""
        return self.cars.get(self.my_user_id)
    
    def get_rankings(self) -> List[CarState]:
        """获取排名"""
        # 按圈数、检查点、距离排序
        def sort_key(car: CarState):
            if car.is_finished:
                return (-1000, car.rank)
            return (-car.lap, -car.checkpoint)
        
        return sorted(self.cars.values(), key=sort_key)
    
    def get_race_progress(self, user_id: str) -> float:
        """获取比赛进度 [0, 1]"""
        car = self.cars.get(user_id)
        if not car or not self.track:
            return 0.0
        
        total = self.track.total_laps * len(self.track.checkpoints)
        current = car.lap * len(self.track.checkpoints) + car.checkpoint
        return min(1.0, current / total)

