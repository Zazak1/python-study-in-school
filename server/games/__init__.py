"""
游戏逻辑模块
"""
from .base import GameLogic
from .gomoku import GomokuGame
from .game_service import GameService

# 游戏逻辑映射
GAME_LOGIC_MAP = {
    'gomoku': GomokuGame,
    # 其他游戏后续添加
}

__all__ = [
    'GameLogic',
    'GomokuGame',
    'GameService',
    'GAME_LOGIC_MAP'
]

