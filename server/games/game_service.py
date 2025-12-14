"""
游戏服务 - 管理所有游戏实例
"""
import asyncio
from typing import Dict, Any, Optional

from .base import GameLogic
from ..models.room import Room, RoomState
from ..models.user import UserStatus
from ..gateway.connection import ConnectionManager
from ..gateway.handler import ServiceRegistry


class GameService:
    """游戏服务"""
    
    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager
        
        # 游戏实例 {room_id: GameLogic}
        self._games: Dict[str, GameLogic] = {}
        
        # 帧同步任务 {room_id: Task}
        self._tick_tasks: Dict[str, asyncio.Task] = {}
    
    def _get_game_class(self, game_type: str):
        """获取游戏逻辑类（避免循环导入）"""
        from . import GAME_LOGIC_MAP
        return GAME_LOGIC_MAP.get(game_type)
    
    async def init_game(self, room: Room) -> bool:
        """初始化游戏"""
        game_type = room.game_type
        
        # 获取游戏逻辑类
        game_class = self._get_game_class(game_type)
        if not game_class:
            print(f"[GameService] 未知的游戏类型: {game_type}")
            return False
        
        # 创建游戏实例
        game = game_class(room)
        self._games[room.room_id] = game
        
        # 初始化游戏状态
        init_data = game.init_game()
        
        # 更新房间状态
        room.state = RoomState.PLAYING
        
        # 广播游戏开始
        await self.conn_manager.send_to_room(room.room_id, init_data)

        # 私有初始化数据（例如狼人杀身份牌）
        for p in room.players:
            try:
                private_init = game.get_private_init(p.user_id)
            except Exception:
                private_init = None
            if private_init:
                await self.conn_manager.send_to_user(p.user_id, private_init)
        
        # 如果是帧同步游戏，启动 tick 任务
        from ..config import GAME_CONFIGS
        game_cfg = GAME_CONFIGS.get(game_type, {})
        tick_rate = game_cfg.get('tick_rate', 0)
        
        if tick_rate > 0:
            task = asyncio.create_task(self._tick_loop(room.room_id, 1.0 / tick_rate))
            self._tick_tasks[room.room_id] = task
        
        print(f"[GameService] 游戏开始: {room.room_id} ({game_type})")
        return True
    
    async def process_action(self, user_id: str, room_id: str, action: str, data: Dict[str, Any]) -> tuple:
        """
        处理游戏行动
        
        Returns:
            (success, result_data)
        """
        game = self._games.get(room_id)
        if not game:
            return False, {"error": "游戏不存在"}
        
        if game.is_finished:
            return False, {"error": "游戏已结束"}
        
        # 服务器权威处理
        success, result, broadcast = game.process_action(user_id, action, data)
        
        if success and broadcast:
            # 广播给所有玩家
            await self.conn_manager.send_to_room(room_id, broadcast)
            
            # 检查游戏结束
            if game.is_finished:
                await self._handle_game_over(room_id, game)
        
        return success, result
    
    async def handle_disconnect(self, user_id: str, room_id: str):
        """处理玩家断线"""
        game = self._games.get(room_id)
        if not game:
            return
        
        result = game.handle_disconnect(user_id)
        
        if result:
            # 兼容旧逻辑：若游戏逻辑未返回 type，则包装为 game_action
            if isinstance(result, dict) and "type" not in result:
                result = {
                    "type": "game_action",
                    "action": "player_disconnected",
                    **result,
                }
            await self.conn_manager.send_to_room(room_id, result)
        
        if game.is_finished:
            await self._handle_game_over(room_id, game)
    
    async def get_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """获取游戏状态（用于重连）"""
        game = self._games.get(room_id)
        if game:
            return game.get_state()
        return None

    def get_private_init(self, room_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """获取单个玩家的私有初始化数据（用于断线重连恢复）。"""
        game = self._games.get(room_id)
        if not game:
            return None
        try:
            return game.get_private_init(user_id)
        except Exception:
            return None
    
    async def _tick_loop(self, room_id: str, dt: float):
        """帧同步循环"""
        try:
            while True:
                await asyncio.sleep(dt)
                
                game = self._games.get(room_id)
                if not game or game.is_finished:
                    break
                
                # 更新游戏
                game.update(dt)
                game.frame_id += 1
                
                # 广播状态
                state = game.get_state()
                await self.conn_manager.send_to_room(room_id, {
                    "type": "game_sync",
                    "frame_id": game.frame_id,
                    "state": state
                })

                # 帧循环中触发的结束（如碰撞判定）需要在此收尾
                if game.is_finished:
                    await self._handle_game_over(room_id, game, cancel_tick=False)
                    break
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[GameService] Tick 循环异常 {room_id}: {e}")
    
    async def _handle_game_over(self, room_id: str, game: GameLogic, cancel_tick: bool = True):
        """处理游戏结束"""
        if room_id not in self._games:
            return

        print(f"[GameService] 游戏结束: {room_id}")
        
        # 停止 tick 任务
        task = self._tick_tasks.pop(room_id, None)
        if task and cancel_tick:
            task.cancel()
        
        # 获取结果
        result = game.check_game_over()
        
        # 广播游戏结束
        await self.conn_manager.send_to_room(room_id, {
            "type": "game_end",
            "winner": result.winner_id if result else None,
            "scores": result.scores if result else {},
            "stats": result.stats if result else {}
        })
        
        # 更新房间状态
        room_service = ServiceRegistry.get("room_service")
        room = None
        if room_service:
            room = room_service.get_room(room_id)
            if room:
                # 对局结束后回到等待状态，便于继续在同房间再次开始/断线恢复房间
                room.state = RoomState.WAITING

                # 更新玩家在线状态：从 IN_GAME 回到 IN_ROOM
                user_service = ServiceRegistry.get("user_service")
                if user_service:
                    for p in room.players:
                        try:
                            await user_service.update_user_status(p.user_id, UserStatus.IN_ROOM, room_id, room.game_type)
                        except Exception:
                            pass

                # 刷新大厅房间列表（对局中 -> 可加入/可开局）
                try:
                    await room_service._broadcast_room_list_update()
                except Exception:
                    pass
        
        # 更新玩家统计
        auth_service = ServiceRegistry.get("auth_service")
        if auth_service and result:
            for user_id, score in result.scores.items():
                user = auth_service.get_user(user_id)
                if user:
                    user.games_played += 1
                    if user_id == result.winner_id:
                        user.games_won += 1
                        user.coins += 50  # 胜利奖励
                    user.exp += score
        
        # 清理游戏实例
        self._games.pop(room_id, None)
    
    def cleanup(self):
        """清理所有游戏"""
        for task in self._tick_tasks.values():
            task.cancel()
        self._tick_tasks.clear()
        self._games.clear()
