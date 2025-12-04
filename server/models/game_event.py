"""
游戏事件模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class EventType(str, Enum):
    """事件类型"""
    # 系统
    HEARTBEAT = "heartbeat"
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
    PLAYER_READY = "player_ready"
    KICK_PLAYER = "kick_player"
    START_GAME = "start_game"
    
    # 匹配
    QUICK_MATCH = "quick_match"
    MATCH_FOUND = "match_found"
    CANCEL_MATCH = "cancel_match"
    
    # 游戏
    GAME_START = "game_start"
    GAME_INPUT = "game_input"
    GAME_STATE = "game_state"
    GAME_ACTION = "game_action"
    GAME_SYNC = "game_sync"
    GAME_END = "game_end"
    
    # 聊天
    CHAT_MESSAGE = "chat_message"
    
    # 通知
    NOTIFICATION = "notification"
    INVITE = "invite"


class GameEvent(BaseModel):
    """游戏事件"""
    type: EventType
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    # 元数据
    event_id: str = ""
    frame_id: int = 0
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    # 发送者（服务器填充）
    sender_id: Optional[str] = None
    room_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class GameInput(BaseModel):
    """游戏输入（客户端发送）"""
    frame_id: int
    inputs: Dict[str, Any]  # 具体输入数据
    timestamp: float


class GameState(BaseModel):
    """游戏状态（服务器广播）"""
    frame_id: int
    state: Dict[str, Any]
    delta: bool = False  # 是否为增量更新
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class ChatMessage(BaseModel):
    """聊天消息"""
    channel: str  # "lobby" / "room" / "team"
    sender_id: str
    sender_name: str
    content: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())

