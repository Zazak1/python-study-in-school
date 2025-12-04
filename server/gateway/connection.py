"""
连接管理
"""
import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, Optional, Set, Any, Callable
from dataclasses import dataclass, field
import websockets
from websockets.server import WebSocketServerProtocol

from ..models.user import UserSession, UserStatus


@dataclass
class Connection:
    """WebSocket 连接"""
    connection_id: str
    websocket: WebSocketServerProtocol
    
    # 用户信息（登录后填充）
    user_id: Optional[str] = None
    user_session: Optional[UserSession] = None
    
    # 连接状态
    is_authenticated: bool = False
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    
    # 订阅的频道
    channels: Set[str] = field(default_factory=set)
    
    async def send(self, data: Dict[str, Any]):
        """发送消息"""
        try:
            await self.websocket.send(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            print(f"[Connection] 发送消息失败 {self.connection_id}: {e}")
    
    async def send_error(self, code: int, message: str):
        """发送错误"""
        await self.send({
            "type": "error",
            "code": code,
            "message": message,
            "timestamp": datetime.now().timestamp()
        })
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()
    
    def is_alive(self, timeout: int = 90) -> bool:
        """检查是否存活"""
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < timeout


class ConnectionManager:
    """连接管理器"""
    
    def __init__(self):
        # 所有连接 {connection_id: Connection}
        self._connections: Dict[str, Connection] = {}
        
        # 用户连接映射 {user_id: connection_id}
        self._user_connections: Dict[str, str] = {}
        
        # 房间连接映射 {room_id: Set[connection_id]}
        self._room_connections: Dict[str, Set[str]] = {}
        
        # 频道订阅 {channel: Set[connection_id]}
        self._channel_subscriptions: Dict[str, Set[str]] = {}
        
        # 锁
        self._lock = asyncio.Lock()
    
    @property
    def connection_count(self) -> int:
        return len(self._connections)
    
    @property
    def authenticated_count(self) -> int:
        return len(self._user_connections)
    
    async def add_connection(self, websocket: WebSocketServerProtocol) -> Connection:
        """添加新连接"""
        connection_id = str(uuid.uuid4())
        connection = Connection(
            connection_id=connection_id,
            websocket=websocket
        )
        
        async with self._lock:
            self._connections[connection_id] = connection
        
        print(f"[ConnectionManager] 新连接: {connection_id}, 总数: {self.connection_count}")
        return connection
    
    async def remove_connection(self, connection_id: str):
        """移除连接"""
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            
            if connection:
                # 移除用户映射
                if connection.user_id:
                    self._user_connections.pop(connection.user_id, None)
                
                # 移除房间映射
                for room_id, conn_ids in list(self._room_connections.items()):
                    conn_ids.discard(connection_id)
                    if not conn_ids:
                        del self._room_connections[room_id]
                
                # 移除频道订阅
                for channel, conn_ids in list(self._channel_subscriptions.items()):
                    conn_ids.discard(connection_id)
                    if not conn_ids:
                        del self._channel_subscriptions[channel]
        
        print(f"[ConnectionManager] 连接断开: {connection_id}, 剩余: {self.connection_count}")
    
    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """获取连接"""
        return self._connections.get(connection_id)
    
    def get_connection_by_user(self, user_id: str) -> Optional[Connection]:
        """通过用户 ID 获取连接"""
        connection_id = self._user_connections.get(user_id)
        if connection_id:
            return self._connections.get(connection_id)
        return None
    
    async def authenticate_connection(self, connection_id: str, user_id: str, session: UserSession):
        """认证连接"""
        async with self._lock:
            connection = self._connections.get(connection_id)
            if connection:
                # 踢掉旧连接
                old_conn_id = self._user_connections.get(user_id)
                if old_conn_id and old_conn_id != connection_id:
                    old_conn = self._connections.get(old_conn_id)
                    if old_conn:
                        await old_conn.send_error(1001, "您已在其他设备登录")
                        await old_conn.websocket.close()
                
                connection.user_id = user_id
                connection.user_session = session
                connection.is_authenticated = True
                self._user_connections[user_id] = connection_id
    
    async def join_room(self, connection_id: str, room_id: str):
        """加入房间"""
        async with self._lock:
            if room_id not in self._room_connections:
                self._room_connections[room_id] = set()
            self._room_connections[room_id].add(connection_id)
    
    async def leave_room(self, connection_id: str, room_id: str):
        """离开房间"""
        async with self._lock:
            if room_id in self._room_connections:
                self._room_connections[room_id].discard(connection_id)
                if not self._room_connections[room_id]:
                    del self._room_connections[room_id]
    
    async def subscribe_channel(self, connection_id: str, channel: str):
        """订阅频道"""
        async with self._lock:
            if channel not in self._channel_subscriptions:
                self._channel_subscriptions[channel] = set()
            self._channel_subscriptions[channel].add(connection_id)
            
            connection = self._connections.get(connection_id)
            if connection:
                connection.channels.add(channel)
    
    async def unsubscribe_channel(self, connection_id: str, channel: str):
        """取消订阅"""
        async with self._lock:
            if channel in self._channel_subscriptions:
                self._channel_subscriptions[channel].discard(connection_id)
            
            connection = self._connections.get(connection_id)
            if connection:
                connection.channels.discard(channel)
    
    # ========== 广播方法 ==========
    
    async def send_to_user(self, user_id: str, data: Dict[str, Any]):
        """发送给指定用户"""
        connection = self.get_connection_by_user(user_id)
        if connection:
            await connection.send(data)
    
    async def send_to_room(self, room_id: str, data: Dict[str, Any], exclude: Optional[str] = None):
        """发送给房间内所有人"""
        conn_ids = self._room_connections.get(room_id, set())
        
        for conn_id in conn_ids:
            if exclude and conn_id == exclude:
                continue
            connection = self._connections.get(conn_id)
            if connection:
                await connection.send(data)
    
    async def send_to_channel(self, channel: str, data: Dict[str, Any], exclude: Optional[str] = None):
        """发送给频道订阅者"""
        conn_ids = self._channel_subscriptions.get(channel, set())
        
        for conn_id in conn_ids:
            if exclude and conn_id == exclude:
                continue
            connection = self._connections.get(conn_id)
            if connection:
                await connection.send(data)
    
    async def broadcast(self, data: Dict[str, Any], authenticated_only: bool = True):
        """广播给所有连接"""
        for connection in self._connections.values():
            if authenticated_only and not connection.is_authenticated:
                continue
            await connection.send(data)
    
    # ========== 清理 ==========
    
    async def cleanup_dead_connections(self, timeout: int = 90):
        """清理死连接"""
        dead_connections = []
        
        for conn_id, connection in self._connections.items():
            if not connection.is_alive(timeout):
                dead_connections.append(conn_id)
        
        for conn_id in dead_connections:
            print(f"[ConnectionManager] 清理超时连接: {conn_id}")
            await self.remove_connection(conn_id)
            
            # 关闭 WebSocket
            connection = self._connections.get(conn_id)
            if connection:
                try:
                    await connection.websocket.close()
                except:
                    pass
        
        return len(dead_connections)

