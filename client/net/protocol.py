"""
网络协议定义 - 消息格式与序列化
"""
import json
import time
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """消息类型"""
    # 系统消息
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    ERROR = "error"
    
    # 认证
    LOGIN = "login"
    LOGIN_RESPONSE = "login_response"
    LOGOUT = "logout"
    
    # 大厅
    FRIEND_LIST = "friend_list"
    FRIEND_STATUS = "friend_status"
    ROOM_LIST = "room_list"
    
    # 房间
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_UPDATE = "room_update"
    ROOM_CHAT = "room_chat"
    KICK_PLAYER = "kick_player"
    START_GAME = "start_game"
    
    # 匹配
    QUICK_MATCH = "quick_match"
    MATCH_FOUND = "match_found"
    CANCEL_MATCH = "cancel_match"
    
    # 游戏
    GAME_INPUT = "game_input"
    GAME_STATE = "game_state"
    GAME_EVENT = "game_event"
    GAME_SYNC = "game_sync"
    GAME_END = "game_end"
    
    # 聊天
    CHAT_MESSAGE = "chat_message"
    CHAT_HISTORY = "chat_history"
    
    # 通知
    NOTIFICATION = "notification"
    INVITE = "invite"


# ========== Pydantic 消息模型 ==========

class BaseMessage(BaseModel):
    """基础消息"""
    type: MessageType
    msg_id: str = ""
    timestamp: float = Field(default_factory=time.time)
    
    class Config:
        use_enum_values = True


class LoginRequest(BaseMessage):
    """登录请求"""
    type: MessageType = MessageType.LOGIN
    username: str
    password: str
    client_version: str
    platform: str  # "windows" / "macos"


class LoginResponse(BaseMessage):
    """登录响应"""
    type: MessageType = MessageType.LOGIN_RESPONSE
    success: bool
    user_id: str = ""
    token: str = ""
    nickname: str = ""
    avatar: str = ""
    coins: int = 0
    error_message: str = ""


class FriendInfo(BaseModel):
    """好友信息"""
    user_id: str
    nickname: str
    avatar: str = ""
    is_online: bool = False
    status: str = ""  # "idle" / "in_game" / "in_room"
    current_game: str = ""


class FriendListMessage(BaseMessage):
    """好友列表"""
    type: MessageType = MessageType.FRIEND_LIST
    friends: List[FriendInfo] = []


class RoomInfo(BaseModel):
    """房间信息"""
    room_id: str
    name: str
    game_type: str
    max_players: int
    current_players: int
    host_id: str
    host_name: str
    is_playing: bool = False
    is_private: bool = False


class RoomListMessage(BaseMessage):
    """房间列表"""
    type: MessageType = MessageType.ROOM_LIST
    rooms: List[RoomInfo] = []


class CreateRoomRequest(BaseMessage):
    """创建房间请求"""
    type: MessageType = MessageType.CREATE_ROOM
    game_type: str
    name: str
    max_players: int
    is_private: bool = False
    password: str = ""


class JoinRoomRequest(BaseMessage):
    """加入房间请求"""
    type: MessageType = MessageType.JOIN_ROOM
    room_id: str
    password: str = ""


class RoomUpdate(BaseMessage):
    """房间状态更新"""
    type: MessageType = MessageType.ROOM_UPDATE
    room: RoomInfo
    players: List[Dict[str, Any]] = []  # 玩家列表
    action: str = ""  # "joined" / "left" / "ready" / "start"


class GameEvent(BaseMessage):
    """游戏事件"""
    type: MessageType = MessageType.GAME_EVENT
    event_type: str  # "move" / "attack" / "item" / etc
    payload: Dict[str, Any] = {}
    frame_id: int = 0
    player_id: str = ""


class GameSync(BaseMessage):
    """游戏状态同步"""
    type: MessageType = MessageType.GAME_SYNC
    frame_id: int
    state: Dict[str, Any]  # 完整或增量状态
    delta: bool = False  # 是否为增量


class ChatMessage(BaseMessage):
    """聊天消息"""
    type: MessageType = MessageType.CHAT_MESSAGE
    channel: str  # "lobby" / "room" / "team"
    sender_id: str
    sender_name: str
    content: str


class NotificationMessage(BaseMessage):
    """通知消息"""
    type: MessageType = MessageType.NOTIFICATION
    title: str
    content: str
    level: str = "info"  # "info" / "warning" / "error" / "success"
    action_url: str = ""


class InviteMessage(BaseMessage):
    """邀请消息"""
    type: MessageType = MessageType.INVITE
    from_user_id: str
    from_nickname: str
    room_id: str
    game_type: str


# ========== 协议工具类 ==========

class Protocol:
    """协议工具"""
    
    MESSAGE_TYPES = {
        MessageType.LOGIN: LoginRequest,
        MessageType.LOGIN_RESPONSE: LoginResponse,
        MessageType.FRIEND_LIST: FriendListMessage,
        MessageType.ROOM_LIST: RoomListMessage,
        MessageType.CREATE_ROOM: CreateRoomRequest,
        MessageType.JOIN_ROOM: JoinRoomRequest,
        MessageType.ROOM_UPDATE: RoomUpdate,
        MessageType.GAME_EVENT: GameEvent,
        MessageType.GAME_SYNC: GameSync,
        MessageType.CHAT_MESSAGE: ChatMessage,
        MessageType.NOTIFICATION: NotificationMessage,
        MessageType.INVITE: InviteMessage,
    }
    
    @staticmethod
    def encode(message: BaseMessage) -> str:
        """编码消息为 JSON"""
        return message.model_dump_json()
    
    @staticmethod
    def decode(data: str) -> Optional[BaseMessage]:
        """解码 JSON 为消息对象"""
        try:
            raw = json.loads(data)
            msg_type = MessageType(raw.get('type'))
            
            model_class = Protocol.MESSAGE_TYPES.get(msg_type)
            if model_class:
                return model_class.model_validate(raw)
            
            # 未知类型返回基础消息
            return BaseMessage.model_validate(raw)
            
        except Exception as e:
            print(f"[Protocol] 解码失败: {e}")
            return None
    
    @staticmethod
    def create_heartbeat() -> str:
        """创建心跳消息"""
        return json.dumps({
            "type": MessageType.HEARTBEAT.value,
            "timestamp": time.time()
        })
    
    @staticmethod
    def create_error(code: int, message: str) -> str:
        """创建错误消息"""
        return json.dumps({
            "type": MessageType.ERROR.value,
            "code": code,
            "message": message,
            "timestamp": time.time()
        })

