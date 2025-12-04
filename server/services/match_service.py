"""
匹配服务
"""
import asyncio
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from ..config import config, GAME_CONFIGS
from ..models.room import Room, RoomPlayer
from ..gateway.connection import ConnectionManager
from ..gateway.handler import ServiceRegistry


@dataclass
class MatchRequest:
    """匹配请求"""
    user_id: str
    game_type: str
    rank_score: int = 1000
    created_at: datetime = field(default_factory=datetime.now)
    
    def wait_time(self) -> float:
        """等待时间（秒）"""
        return (datetime.now() - self.created_at).total_seconds()


class MatchService:
    """匹配服务"""
    
    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager
        
        # 匹配队列 {game_type: [MatchRequest]}
        self._queues: Dict[str, List[MatchRequest]] = {}
        
        # 正在匹配的用户
        self._matching_users: Set[str] = set()
        
        # 匹配任务
        self._match_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """启动匹配服务"""
        self._running = True
        self._match_task = asyncio.create_task(self._match_loop())
        print("[MatchService] 匹配服务已启动")
    
    async def stop(self):
        """停止匹配服务"""
        self._running = False
        if self._match_task:
            self._match_task.cancel()
            try:
                await self._match_task
            except asyncio.CancelledError:
                pass
        print("[MatchService] 匹配服务已停止")
    
    async def request_match(self, user_id: str, game_type: str) -> tuple:
        """
        请求匹配
        
        Returns:
            (success, message)
        """
        # 检查游戏类型
        if game_type not in GAME_CONFIGS:
            return False, "不支持的游戏类型"
        
        # 检查是否已在匹配
        if user_id in self._matching_users:
            return False, "已在匹配队列中"
        
        # 获取用户段位分
        auth_service = ServiceRegistry.get("auth_service")
        rank_score = 1000
        if auth_service:
            user = auth_service.get_user(user_id)
            if user:
                rank_score = user.rank_score
        
        # 创建匹配请求
        request = MatchRequest(
            user_id=user_id,
            game_type=game_type,
            rank_score=rank_score
        )
        
        # 加入队列
        if game_type not in self._queues:
            self._queues[game_type] = []
        self._queues[game_type].append(request)
        self._matching_users.add(user_id)
        
        # 通知用户
        await self.conn_manager.send_to_user(user_id, {
            "type": "match_queued",
            "game_type": game_type,
            "queue_size": len(self._queues[game_type])
        })
        
        return True, "已加入匹配队列"
    
    async def cancel_match(self, user_id: str) -> bool:
        """取消匹配"""
        if user_id not in self._matching_users:
            return False
        
        # 从所有队列中移除
        for queue in self._queues.values():
            queue[:] = [r for r in queue if r.user_id != user_id]
        
        self._matching_users.discard(user_id)
        
        await self.conn_manager.send_to_user(user_id, {
            "type": "match_cancelled"
        })
        
        return True
    
    async def _match_loop(self):
        """匹配循环"""
        while self._running:
            try:
                await asyncio.sleep(config.match_check_interval)
                
                for game_type, queue in list(self._queues.items()):
                    if not queue:
                        continue
                    
                    await self._try_match(game_type, queue)
                    
                    # 清理超时请求
                    await self._cleanup_timeout(game_type, queue)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[MatchService] 匹配循环异常: {e}")
    
    async def _try_match(self, game_type: str, queue: List[MatchRequest]):
        """尝试匹配"""
        game_cfg = GAME_CONFIGS.get(game_type)
        if not game_cfg:
            return
        
        min_players = game_cfg['min_players']
        max_players = game_cfg['max_players']
        
        # 按段位分排序
        queue.sort(key=lambda x: x.rank_score)
        
        # 简单匹配：够人数就匹配
        while len(queue) >= min_players:
            # 取前 max_players 个
            matched = queue[:max_players]
            
            # 检查段位差距（可选，放宽限制）
            # 这里简单实现，只检查等待时间超过一定值后放宽匹配
            
            # 创建房间
            await self._create_match_room(game_type, matched)
            
            # 从队列移除
            for req in matched:
                queue.remove(req)
                self._matching_users.discard(req.user_id)
    
    async def _create_match_room(self, game_type: str, requests: List[MatchRequest]):
        """创建匹配房间"""
        room_service = ServiceRegistry.get("room_service")
        auth_service = ServiceRegistry.get("auth_service")
        
        if not room_service or not auth_service:
            return
        
        # 第一个玩家作为房主创建房间
        host_request = requests[0]
        host_user = auth_service.get_user(host_request.user_id)
        if not host_user:
            return
        
        # 创建房间
        room = await room_service.create_room(
            user_id=host_request.user_id,
            game_type=game_type,
            name=f"匹配房间 #{uuid.uuid4().hex[:4]}",
            max_players=len(requests)
        )
        
        if not room:
            return
        
        # 其他玩家加入
        for req in requests[1:]:
            await room_service.join_room(req.user_id, room.room_id)
            
            # 自动准备
            player = room.get_player(req.user_id)
            if player:
                player.is_ready = True
        
        # 通知所有玩家
        for req in requests:
            await self.conn_manager.send_to_user(req.user_id, {
                "type": "match_found",
                "room_id": room.room_id,
                "game_type": game_type,
                "players": [r.user_id for r in requests]
            })
        
        # 自动开始游戏
        await asyncio.sleep(3)  # 等待 3 秒
        if room.can_start:
            await room_service.start_game(host_request.user_id, room.room_id)
    
    async def _cleanup_timeout(self, game_type: str, queue: List[MatchRequest]):
        """清理超时请求"""
        timeout_requests = [r for r in queue if r.wait_time() > config.match_timeout]
        
        for req in timeout_requests:
            queue.remove(req)
            self._matching_users.discard(req.user_id)
            
            await self.conn_manager.send_to_user(req.user_id, {
                "type": "match_timeout",
                "game_type": game_type
            })

