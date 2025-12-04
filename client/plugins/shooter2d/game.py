"""
2D 射击游戏实现
"""
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
import math
from ..base import (
    GamePlugin, GameContext, RoomState, NetworkEvent,
    GameState, EventType
)


@dataclass
class Vector2:
    """2D 向量"""
    x: float = 0.0
    y: float = 0.0
    
    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x * scalar, self.y * scalar)
    
    def length(self) -> float:
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalize(self) -> 'Vector2':
        l = self.length()
        if l > 0:
            return Vector2(self.x / l, self.y / l)
        return Vector2()


@dataclass
class Player:
    """玩家实体"""
    user_id: str
    position: Vector2 = field(default_factory=Vector2)
    velocity: Vector2 = field(default_factory=Vector2)
    rotation: float = 0.0  # 角度
    health: int = 100
    is_alive: bool = True
    team_id: int = 0


@dataclass  
class Bullet:
    """子弹实体"""
    bullet_id: str
    owner_id: str
    position: Vector2 = field(default_factory=Vector2)
    velocity: Vector2 = field(default_factory=Vector2)
    damage: int = 10
    is_active: bool = True


@dataclass
class Obstacle:
    """障碍物"""
    position: Vector2 = field(default_factory=Vector2)
    width: float = 50.0
    height: float = 50.0


class Shooter2DPlugin(GamePlugin):
    """2D 射击游戏插件"""
    
    PLUGIN_NAME = "shooter2d"
    PLUGIN_VERSION = "0.1.0"
    PLUGIN_DESCRIPTION = "紧张刺激的 2D 射击对战"
    MIN_PLAYERS = 2
    MAX_PLAYERS = 8
    SUPPORTS_SPECTATE = True
    
    # 游戏设置
    MAP_WIDTH = 1920
    MAP_HEIGHT = 1080
    PLAYER_SPEED = 200.0
    BULLET_SPEED = 500.0
    FIRE_COOLDOWN = 0.2  # 射击冷却（秒）
    
    def __init__(self):
        super().__init__()
        self._players: Dict[str, Player] = {}
        self._bullets: Dict[str, Bullet] = {}
        self._obstacles: List[Obstacle] = []
        self._local_player_id: str = ""
        
        # 输入状态
        self._keys_pressed: Set[str] = set()
        self._mouse_position: Vector2 = Vector2()
        self._fire_cooldown: float = 0.0
        
        # 客户端预测
        self._pending_inputs: List[Dict] = []
        self._last_server_frame: int = 0
    
    def load(self, context: GameContext) -> bool:
        """加载游戏资源"""
        self._context = context
        self._state = GameState.LOADING
        
        if context.local_user:
            self._local_player_id = context.local_user.user_id
        
        # TODO: 加载纹理、音效等资源
        
        self._state = GameState.READY
        self._is_loaded = True
        return True
    
    def join_room(self, room_state: RoomState) -> bool:
        """加入房间"""
        self._room_state = room_state
        self._players.clear()
        self._bullets.clear()
        
        # 初始化玩家
        for player_info in room_state.current_players:
            self._players[player_info.user_id] = Player(
                user_id=player_info.user_id,
                team_id=player_info.team_id or 0
            )
        
        return True
    
    def start_game(self) -> bool:
        """开始游戏"""
        self._state = GameState.PLAYING
        self._fire_cooldown = 0.0
        return True
    
    def dispose(self) -> None:
        """清理资源"""
        self._players.clear()
        self._bullets.clear()
        self._obstacles.clear()
        self._keys_pressed.clear()
        self._pending_inputs.clear()
        self._state = GameState.IDLE
        self._is_loaded = False
    
    def update(self, dt: float) -> None:
        """游戏帧更新"""
        if self._state != GameState.PLAYING:
            return
        
        # 更新射击冷却
        if self._fire_cooldown > 0:
            self._fire_cooldown -= dt
        
        # 客户端预测：处理本地输入
        self._process_local_input(dt)
        
        # 更新子弹位置
        self._update_bullets(dt)
        
        self._frame_id += 1
    
    def _process_local_input(self, dt: float) -> None:
        """处理本地输入（客户端预测）"""
        if self._local_player_id not in self._players:
            return
        
        local_player = self._players[self._local_player_id]
        if not local_player.is_alive:
            return
        
        # 计算移动方向
        move_dir = Vector2()
        if 'w' in self._keys_pressed or 'up' in self._keys_pressed:
            move_dir.y += 1
        if 's' in self._keys_pressed or 'down' in self._keys_pressed:
            move_dir.y -= 1
        if 'a' in self._keys_pressed or 'left' in self._keys_pressed:
            move_dir.x -= 1
        if 'd' in self._keys_pressed or 'right' in self._keys_pressed:
            move_dir.x += 1
        
        # 归一化并应用速度
        if move_dir.length() > 0:
            move_dir = move_dir.normalize()
            velocity = move_dir * self.PLAYER_SPEED
            
            # 客户端预测移动
            local_player.position = local_player.position + velocity * dt
            
            # 边界检查
            local_player.position.x = max(0, min(self.MAP_WIDTH, local_player.position.x))
            local_player.position.y = max(0, min(self.MAP_HEIGHT, local_player.position.y))
            
            # 发送输入到服务器
            self.send_input({
                "type": "move",
                "dx": move_dir.x,
                "dy": move_dir.y,
                "frame": self._frame_id
            })
        
        # 计算朝向（面向鼠标）
        dx = self._mouse_position.x - local_player.position.x
        dy = self._mouse_position.y - local_player.position.y
        local_player.rotation = math.degrees(math.atan2(dy, dx))
    
    def _update_bullets(self, dt: float) -> None:
        """更新子弹"""
        bullets_to_remove = []
        
        for bullet_id, bullet in self._bullets.items():
            if not bullet.is_active:
                bullets_to_remove.append(bullet_id)
                continue
            
            # 更新位置
            bullet.position = bullet.position + bullet.velocity * dt
            
            # 检查边界
            if (bullet.position.x < 0 or bullet.position.x > self.MAP_WIDTH or
                bullet.position.y < 0 or bullet.position.y > self.MAP_HEIGHT):
                bullets_to_remove.append(bullet_id)
        
        for bullet_id in bullets_to_remove:
            del self._bullets[bullet_id]
    
    def render(self, surface: Any) -> None:
        """渲染当前帧"""
        # 渲染逻辑由 arcade/UI 层实现
        pass
    
    def on_network(self, event: NetworkEvent) -> None:
        """处理网络事件"""
        if event.type == EventType.SYNC:
            self._handle_sync(event.payload, event.frame_id)
        elif event.type == EventType.STATE:
            self._handle_state_update(event.payload)
        elif event.type == EventType.RECONCILE:
            self._handle_reconciliation(event.payload, event.frame_id)
    
    def _handle_sync(self, payload: Dict, server_frame: int) -> None:
        """处理帧同步"""
        self._last_server_frame = server_frame
        
        # 更新所有玩家状态
        if "players" in payload:
            for player_data in payload["players"]:
                user_id = player_data.get("user_id")
                if user_id in self._players:
                    player = self._players[user_id]
                    player.position.x = player_data.get("x", player.position.x)
                    player.position.y = player_data.get("y", player.position.y)
                    player.rotation = player_data.get("rotation", player.rotation)
                    player.health = player_data.get("health", player.health)
                    player.is_alive = player_data.get("is_alive", player.is_alive)
        
        # 更新子弹
        if "bullets" in payload:
            self._bullets.clear()
            for bullet_data in payload["bullets"]:
                bullet_id = bullet_data.get("id")
                self._bullets[bullet_id] = Bullet(
                    bullet_id=bullet_id,
                    owner_id=bullet_data.get("owner_id", ""),
                    position=Vector2(bullet_data.get("x", 0), bullet_data.get("y", 0)),
                    velocity=Vector2(bullet_data.get("vx", 0), bullet_data.get("vy", 0)),
                    damage=bullet_data.get("damage", 10)
                )
    
    def _handle_state_update(self, payload: Dict) -> None:
        """处理状态更新"""
        action = payload.get("action")
        
        if action == "player_hit":
            target_id = payload.get("target_id")
            damage = payload.get("damage", 10)
            if target_id in self._players:
                self._players[target_id].health -= damage
                if self._players[target_id].health <= 0:
                    self._players[target_id].is_alive = False
        
        elif action == "player_respawn":
            user_id = payload.get("user_id")
            if user_id in self._players:
                self._players[user_id].health = 100
                self._players[user_id].is_alive = True
                self._players[user_id].position = Vector2(
                    payload.get("x", 0),
                    payload.get("y", 0)
                )
        
        elif action == "game_over":
            self._winner = payload.get("winner_team", 0)
            self._state = GameState.FINISHED
    
    def _handle_reconciliation(self, payload: Dict, server_frame: int) -> None:
        """处理服务器状态纠正"""
        # 服务器权威：接受服务器的状态
        if self._local_player_id in self._players:
            player = self._players[self._local_player_id]
            player.position.x = payload.get("x", player.position.x)
            player.position.y = payload.get("y", player.position.y)
            
            # 清除已确认的输入
            self._pending_inputs = [
                inp for inp in self._pending_inputs 
                if inp.get("frame", 0) > server_frame
            ]
            
            # 重放未确认的输入
            for inp in self._pending_inputs:
                self._apply_input(player, inp)
    
    def _apply_input(self, player: Player, input_data: Dict) -> None:
        """应用输入到玩家"""
        if input_data.get("type") == "move":
            dx = input_data.get("dx", 0)
            dy = input_data.get("dy", 0)
            # 简化：假设固定 dt
            dt = 1 / 60
            player.position.x += dx * self.PLAYER_SPEED * dt
            player.position.y += dy * self.PLAYER_SPEED * dt
    
    # ==================== 输入事件 ====================
    
    def on_key_down(self, key: str) -> None:
        """键盘按下"""
        self._keys_pressed.add(key.lower())
    
    def on_key_up(self, key: str) -> None:
        """键盘释放"""
        self._keys_pressed.discard(key.lower())
    
    def on_mouse_move(self, x: int, y: int) -> None:
        """鼠标移动"""
        self._mouse_position = Vector2(x, y)
    
    def on_mouse_down(self, button: int, x: int, y: int) -> None:
        """鼠标按下"""
        if button == 1 and self._fire_cooldown <= 0:
            self._fire()
            self._fire_cooldown = self.FIRE_COOLDOWN
    
    def _fire(self) -> None:
        """发射子弹"""
        if self._local_player_id not in self._players:
            return
        
        player = self._players[self._local_player_id]
        if not player.is_alive:
            return
        
        # 计算子弹方向
        rad = math.radians(player.rotation)
        direction = Vector2(math.cos(rad), math.sin(rad))
        
        # 发送射击请求到服务器
        self.send_input({
            "type": "fire",
            "x": player.position.x,
            "y": player.position.y,
            "dx": direction.x,
            "dy": direction.y,
            "frame": self._frame_id
        })
    
    # ==================== 状态获取 ====================
    
    def get_game_state(self) -> Dict[str, Any]:
        """获取游戏状态供 UI 层使用"""
        return {
            "players": [
                {
                    "user_id": p.user_id,
                    "x": p.position.x,
                    "y": p.position.y,
                    "rotation": p.rotation,
                    "health": p.health,
                    "is_alive": p.is_alive,
                    "is_local": p.user_id == self._local_player_id
                }
                for p in self._players.values()
            ],
            "bullets": [
                {
                    "id": b.bullet_id,
                    "x": b.position.x,
                    "y": b.position.y,
                    "owner_id": b.owner_id
                }
                for b in self._bullets.values()
            ],
            "local_player_id": self._local_player_id,
            "frame_id": self._frame_id
        }

