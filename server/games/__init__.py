"""
游戏逻辑模块
"""
from .base import GameLogic
from .gomoku import GomokuGame
from .shooter2d import Shooter2DGame
from .werewolf import WerewolfGame
from .monopoly import MonopolyGame
from .racing import RacingGame

# 游戏逻辑映射
GAME_LOGIC_MAP = {
    'gomoku': GomokuGame,
    'shooter2d': Shooter2DGame,
    'werewolf': WerewolfGame,
    'monopoly': MonopolyGame,
    'racing': RacingGame,
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
