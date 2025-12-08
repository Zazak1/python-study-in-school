"""
网络模块 - WebSocket 管理、重连、心跳、可靠消息封装
"""
from .websocket_client import WebSocketClient, ConnectionState, Message
from .protocol import (
    MessageType, Protocol,
    LoginRequest, LoginResponse,
    JoinRoomRequest, RoomUpdate,
    GameEvent, ChatMessage
)
from .auth import AuthManager
from .ws_manager import WebSocketManager

__all__ = [
    'WebSocketClient', 'ConnectionState', 'Message',
    'MessageType', 'Protocol',
    'LoginRequest', 'LoginResponse',
    'JoinRoomRequest', 'RoomUpdate',
    'GameEvent', 'ChatMessage',
    'AuthManager', 'WebSocketManager'
]
