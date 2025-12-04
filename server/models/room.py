"""
房间模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class RoomState(str, Enum):
    """房间状态"""
    WAITING = "waiting"      # 等待玩家
    STARTING = "starting"    # 开始倒计时
    PLAYING = "playing"      # 游戏中
    FINISHED = "finished"    # 已结束
    CLOSED = "closed"        # 已关闭


class RoomPlayer(BaseModel):
    """房间内玩家"""
    user_id: str
    nickname: str
    avatar: str = "👤"
    
    is_host: bool = False
    is_ready: bool = False
    team: int = 0  # 队伍编号
    slot: int = 0  # 座位号
    
    # 游戏内数据
    score: int = 0
    is_alive: bool = True
    
    joined_at: datetime = Field(default_factory=datetime.now)


class Room(BaseModel):
    """房间模型"""
    room_id: str
    name: str
    game_type: str
    
    # 配置
    max_players: int = 8
    min_players: int = 2
    is_private: bool = False
    password: str = ""
    
    # 状态
    state: RoomState = RoomState.WAITING
    players: List[RoomPlayer] = Field(default_factory=list)
    spectators: List[str] = Field(default_factory=list)  # 观战者 user_id 列表
    
    # 房主
    host_id: str = ""
    
    # 游戏设置
    game_settings: Dict[str, Any] = Field(default_factory=dict)
    
    # 游戏状态（游戏进行时）
    game_state: Optional[Dict[str, Any]] = None
    current_frame: int = 0
    
    # 时间
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    
    @property
    def current_players(self) -> int:
        return len(self.players)
    
    @property
    def is_full(self) -> bool:
        return self.current_players >= self.max_players
    
    @property
    def can_start(self) -> bool:
        """是否可以开始游戏"""
        if self.current_players < self.min_players:
            return False
        # 检查所有玩家是否准备
        return all(p.is_ready or p.is_host for p in self.players)
    
    def get_player(self, user_id: str) -> Optional[RoomPlayer]:
        """获取玩家"""
        for p in self.players:
            if p.user_id == user_id:
                return p
        return None
    
    def add_player(self, player: RoomPlayer) -> bool:
        """添加玩家"""
        if self.is_full:
            return False
        if self.get_player(player.user_id):
            return False
        
        # 分配座位
        used_slots = {p.slot for p in self.players}
        for i in range(self.max_players):
            if i not in used_slots:
                player.slot = i
                break
        
        # 第一个玩家为房主
        if not self.players:
            player.is_host = True
            self.host_id = player.user_id
        
        self.players.append(player)
        return True
    
    def remove_player(self, user_id: str) -> Optional[RoomPlayer]:
        """移除玩家"""
        for i, p in enumerate(self.players):
            if p.user_id == user_id:
                removed = self.players.pop(i)
                
                # 如果房主离开，转移房主
                if removed.is_host and self.players:
                    self.players[0].is_host = True
                    self.host_id = self.players[0].user_id
                
                return removed
        return None
    
    def to_public_dict(self) -> Dict[str, Any]:
        """转换为公开信息（不含密码等）"""
        host = self.get_player(self.host_id)
        return {
            'room_id': self.room_id,
            'name': self.name,
            'game_type': self.game_type,
            'max_players': self.max_players,
            'current_players': self.current_players,
            'host_name': host.nickname if host else 'Unknown',
            'is_private': self.is_private,
            'is_playing': self.state == RoomState.PLAYING,
        }

