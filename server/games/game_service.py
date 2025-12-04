"""
游戏服务 - 管理所有游戏实例
"""
import asyncio
from typing import Dict, Any, Optional

from .base import GameLogic
from . import GAME_LOGIC_MAP
from ..models.room import Room, RoomState
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
    
    async def init_game(self, room: Room) -> bool:
        """初始化游戏"""
        game_type = room.game_type
        
        # 获取游戏逻辑类
        game_class = GAME_LOGIC_MAP.get(game_type)
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
            await self.conn_manager.send_to_room(room_id, result)
        
        if game.is_finished:
            await self._handle_game_over(room_id, game)
    
    async def get_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """获取游戏状态（用于重连）"""
        game = self._games.get(room_id)
        if game:
            return game.get_state()
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
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[GameService] Tick 循环异常 {room_id}: {e}")
    
    async def _handle_game_over(self, room_id: str, game: GameLogic):
        """处理游戏结束"""
        print(f"[GameService] 游戏结束: {room_id}")
        
        # 停止 tick 任务
        task = self._tick_tasks.pop(room_id, None)
        if task:
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
        if room_service:
            room = room_service.get_room(room_id)
            if room:
                room.state = RoomState.FINISHED
        
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
        del self._games[room_id]
    
    def cleanup(self):
        """清理所有游戏"""
        for task in self._tick_tasks.values():
            task.cancel()
        self._tick_tasks.clear()
        self._games.clear()

