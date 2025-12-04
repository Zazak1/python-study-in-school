"""
游戏逻辑基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..models.room import Room


@dataclass
class GameResult:
    """游戏结果"""
    winner_id: Optional[str] = None  # None 表示平局
    scores: Dict[str, int] = None    # 玩家得分
    stats: Dict[str, Any] = None     # 统计数据


class GameLogic(ABC):
    """游戏逻辑基类（服务器权威）"""
    
    GAME_TYPE: str = "base"
    
    def __init__(self, room: Room):
        self.room = room
        self.state: Dict[str, Any] = {}
        self.current_player: Optional[str] = None
        self.winner: Optional[str] = None
        self.is_finished: bool = False
        self.frame_id: int = 0
    
    @abstractmethod
    def init_game(self) -> Dict[str, Any]:
        """
        初始化游戏状态
        
        Returns:
            初始状态数据（发送给所有玩家）
        """
        pass
    
    @abstractmethod
    def process_action(self, user_id: str, action: str, data: Dict[str, Any]) -> tuple:
        """
        处理玩家行动（服务器权威验证）
        
        Args:
            user_id: 玩家 ID
            action: 行动类型
            data: 行动数据
            
        Returns:
            (success, result_data, broadcast_data)
            - success: 是否成功
            - result_data: 返回给发送者的数据
            - broadcast_data: 广播给所有玩家的数据
        """
        pass
    
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        获取当前游戏状态
        
        Returns:
            状态数据（用于断线重连等）
        """
        pass
    
    @abstractmethod
    def check_game_over(self) -> Optional[GameResult]:
        """
        检查游戏是否结束
        
        Returns:
            GameResult 如果游戏结束，否则 None
        """
        pass
    
    def update(self, dt: float):
        """
        游戏更新（帧同步游戏使用）
        
        Args:
            dt: 时间增量（秒）
        """
        pass
    
    def handle_disconnect(self, user_id: str) -> Dict[str, Any]:
        """
        处理玩家断线
        
        Returns:
            处理结果数据
        """
        return {"disconnected": user_id}
    
    def handle_reconnect(self, user_id: str) -> Dict[str, Any]:
        """
        处理玩家重连
        
        Returns:
            重连数据（当前状态等）
        """
        return self.get_state()

