"""
游戏逻辑模块
"""
from .base import GameLogic
from .gomoku import GomokuGame

# 游戏逻辑映射
GAME_LOGIC_MAP = {
    'gomoku': GomokuGame,
    # 其他游戏后续添加
}

# 延迟导入 GameService 避免循环引用
def get_game_service():
    from .game_service import GameService
    return GameService

__all__ = [
    'GameLogic',
    'GomokuGame',
    'GAME_LOGIC_MAP',
    'get_game_service'
]
