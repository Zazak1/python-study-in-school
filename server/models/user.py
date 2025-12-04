"""
用户模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class UserStatus(str, Enum):
    """用户状态"""
    OFFLINE = "offline"
    ONLINE = "online"
    IN_ROOM = "in_room"
    IN_GAME = "in_game"
    AWAY = "away"


class User(BaseModel):
    """用户模型"""
    user_id: str
    username: str
    nickname: str
    avatar: str = "👤"
    
    # 游戏数据
    level: int = 1
    exp: int = 0
    coins: int = 1000
    
    # 段位
    rank_score: int = 1000  # Elo/TrueSkill 分数
    rank_tier: str = "bronze"  # bronze/silver/gold/platinum/diamond
    
    # 统计
    games_played: int = 0
    games_won: int = 0
    
    # 社交
    friends: List[str] = Field(default_factory=list)
    blocked: List[str] = Field(default_factory=list)
    
    # 时间
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    
    def win_rate(self) -> float:
        """胜率"""
        if self.games_played == 0:
            return 0.0
        return self.games_won / self.games_played


class UserSession(BaseModel):
    """用户会话（在线状态）"""
    user_id: str
    connection_id: str  # WebSocket 连接 ID
    
    status: UserStatus = UserStatus.ONLINE
    current_room: Optional[str] = None
    current_game: Optional[str] = None
    
    # 连接信息
    ip_address: str = ""
    client_version: str = ""
    platform: str = ""  # windows/macos
    
    # 时间
    connected_at: datetime = Field(default_factory=datetime.now)
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    
    def is_alive(self, timeout: int = 90) -> bool:
        """检查连接是否存活"""
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < timeout

