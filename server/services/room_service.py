"""
房间服务
"""
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..config import config, GAME_CONFIGS
from ..models.room import Room, RoomState, RoomPlayer
from ..models.user import UserStatus
from ..gateway.connection import ConnectionManager
from ..gateway.handler import ServiceRegistry


class RoomService:
    """房间服务"""
    
    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager
        self._rooms: Dict[str, Room] = {}
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """获取房间"""
        return self._rooms.get(room_id)
    
    def get_rooms_list(self, game_type: str = None) -> List[Dict[str, Any]]:
        """获取房间列表"""
        rooms = []
        for room in self._rooms.values():
            if room.state in [RoomState.CLOSED, RoomState.FINISHED]:
                continue
            if game_type and room.game_type != game_type:
                continue
            rooms.append(room.to_public_dict())
        
        # 按创建时间排序
        rooms.sort(key=lambda x: x.get('room_id', ''), reverse=True)
        return rooms

    def find_room_by_user(self, user_id: str) -> Optional[Room]:
        """查找用户所在房间（用于断线重连恢复）。"""
        for room in self._rooms.values():
            if room.get_player(user_id):
                return room
        return None
    
    async def create_room(self, user_id: str, game_type: str, name: str, 
                         max_players: int = None, is_private: bool = False,
                         password: str = "") -> Optional[Room]:
        """创建房间"""
        # 验证游戏类型
        game_cfg = GAME_CONFIGS.get(game_type)
        if not game_cfg:
            return None
        
        # 检查房间数量限制
        if len(self._rooms) >= config.max_rooms:
            return None
        
        # 获取用户信息
        auth_service = ServiceRegistry.get("auth_service")
        if not auth_service:
            return None
        
        user = auth_service.get_user(user_id)
        if not user:
            return None
        
        # 确定最大玩家数
        if max_players is None:
            max_players = game_cfg['max_players']
        max_players = min(max_players, game_cfg['max_players'])
        max_players = max(max_players, game_cfg['min_players'])
        
        # 创建房间
        room_id = str(uuid.uuid4())[:8]
        room = Room(
            room_id=room_id,
            name=name or f"{game_cfg['name']}房间",
            game_type=game_type,
            max_players=max_players,
            min_players=game_cfg['min_players'],
            is_private=is_private,
            password=password,
            host_id=user_id
        )
        
        # 房主加入
        player = RoomPlayer(
            user_id=user_id,
            nickname=user.nickname,
            avatar=user.avatar,
            is_host=True,
            is_ready=True  # 房主默认准备
        )
        room.add_player(player)
        
        self._rooms[room_id] = room
        
        # 更新用户状态
        user_service = ServiceRegistry.get("user_service")
        if user_service:
            await user_service.update_user_status(user_id, UserStatus.IN_ROOM, room_id, game_type)
        
        # 加入房间连接组
        conn = self.conn_manager.get_connection_by_user(user_id)
        if conn:
            await self.conn_manager.join_room(conn.connection_id, room_id)
        
        # 广播房间列表更新
        await self._broadcast_room_list_update()
        
        return room
    
    async def join_room(self, user_id: str, room_id: str, password: str = "") -> tuple:
        """
        加入房间
        
        Returns:
            (success, room_or_error)
        """
        room = self._rooms.get(room_id)
        if not room:
            return False, "房间不存在"
        
        if room.state != RoomState.WAITING:
            return False, "房间已开始游戏"
        
        if room.is_full:
            return False, "房间已满"
        
        if room.is_private and room.password and room.password != password:
            return False, "密码错误"
        
        # 获取用户信息
        auth_service = ServiceRegistry.get("auth_service")
        if not auth_service:
            return False, "服务错误"
        
        user = auth_service.get_user(user_id)
        if not user:
            return False, "用户不存在"
        
        # 检查是否已在房间中
        if room.get_player(user_id):
            return False, "已在房间中"
        
        # 加入房间
        player = RoomPlayer(
            user_id=user_id,
            nickname=user.nickname,
            avatar=user.avatar
        )
        
        if not room.add_player(player):
            return False, "加入失败"
        
        # 更新用户状态
        user_service = ServiceRegistry.get("user_service")
        if user_service:
            await user_service.update_user_status(user_id, UserStatus.IN_ROOM, room_id, room.game_type)
        
        # 加入连接组
        conn = self.conn_manager.get_connection_by_user(user_id)
        if conn:
            await self.conn_manager.join_room(conn.connection_id, room_id)
        
        # 通知房间内其他玩家
        await self._broadcast_room_update(room, "player_joined", {
            "user_id": user_id,
            "nickname": user.nickname
        })
        
        # 广播房间列表更新
        await self._broadcast_room_list_update()
        
        return True, room
    
    async def leave_room(self, user_id: str, room_id: str) -> bool:
        """离开房间"""
        room = self._rooms.get(room_id)
        if not room:
            return False
        
        removed = room.remove_player(user_id)
        if not removed:
            return False
        
        # 离开连接组
        conn = self.conn_manager.get_connection_by_user(user_id)
        if conn:
            await self.conn_manager.leave_room(conn.connection_id, room_id)
        
        # 更新用户状态
        user_service = ServiceRegistry.get("user_service")
        if user_service:
            await user_service.update_user_status(user_id, UserStatus.ONLINE, None, None)
        
        # 如果房间空了，删除房间
        if not room.players:
            room.state = RoomState.CLOSED
            del self._rooms[room_id]
        else:
            # 通知房间内其他玩家
            await self._broadcast_room_update(room, "player_left", {
                "user_id": user_id,
                "new_host": room.host_id
            })
        
        # 广播房间列表更新
        await self._broadcast_room_list_update()
        
        return True
    
    async def set_ready(self, user_id: str, room_id: str, is_ready: bool) -> bool:
        """设置准备状态"""
        room = self._rooms.get(room_id)
        if not room:
            return False
        
        player = room.get_player(user_id)
        if not player:
            return False
        
        if player.is_host:
            return False  # 房主不需要准备
        
        player.is_ready = is_ready
        
        await self._broadcast_room_update(room, "player_ready", {
            "user_id": user_id,
            "is_ready": is_ready,
            "can_start": room.can_start
        })
        
        return True
    
    async def start_game(self, user_id: str, room_id: str) -> tuple:
        """开始游戏"""
        room = self._rooms.get(room_id)
        if not room:
            return False, "房间不存在"
        
        if room.host_id != user_id:
            return False, "只有房主可以开始游戏"
        
        if not room.can_start:
            return False, "无法开始，请等待所有玩家准备"
        
        room.state = RoomState.STARTING
        room.started_at = datetime.now()
        
        # 更新所有玩家状态
        user_service = ServiceRegistry.get("user_service")
        for player in room.players:
            if user_service:
                await user_service.update_user_status(
                    player.user_id, UserStatus.IN_GAME, room_id, room.game_type
                )
        
        # 通知游戏服务初始化
        game_service = ServiceRegistry.get("game_service")
        if game_service:
            await game_service.init_game(room)
        
        # 通知房间内玩家
        await self._broadcast_room_update(room, "game_starting", {
            "countdown": 3
        })
        
        # 广播房间列表更新
        await self._broadcast_room_list_update()
        
        return True, room
    
    async def handle_disconnect(self, user_id: str, room_id: str):
        """处理玩家断线"""
        room = self._rooms.get(room_id)
        if not room:
            return
        
        if room.state == RoomState.PLAYING:
            # 游戏中断线，通知游戏服务
            game_service = ServiceRegistry.get("game_service")
            if game_service:
                await game_service.handle_disconnect(user_id, room_id)
        else:
            # 等待中断线，直接离开房间
            await self.leave_room(user_id, room_id)
    
    async def _broadcast_room_update(self, room: Room, action: str, data: Dict[str, Any] = None):
        """广播房间更新"""
        message = {
            "type": "room_update",
            "room_id": room.room_id,
            "action": action,
            "room": room.to_public_dict(),
            "players": [
                {
                    "user_id": p.user_id,
                    "nickname": p.nickname,
                    "avatar": p.avatar,
                    "is_host": p.is_host,
                    "is_ready": p.is_ready,
                    "slot": p.slot
                }
                for p in room.players
            ]
        }
        if data:
            message.update(data)
        
        await self.conn_manager.send_to_room(room.room_id, message)
    
    async def _broadcast_room_list_update(self):
        """广播房间列表更新"""
        rooms = self.get_rooms_list()
        await self.conn_manager.send_to_channel("lobby", {
            "type": "room_list",
            "rooms": rooms
        })
