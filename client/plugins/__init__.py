"""
游戏插件模块
"""
from .base import GamePlugin
from .gomoku import GomokuPlugin
from .shooter2d import Shooter2DPlugin
from .werewolf import WerewolfPlugin
from .monopoly import MonopolyPlugin
from .racing import RacingPlugin

# 已注册的游戏插件
GAME_PLUGINS = {
    'gomoku': GomokuPlugin,
    'shooter2d': Shooter2DPlugin,
    'werewolf': WerewolfPlugin,
    'monopoly': MonopolyPlugin,
    'racing': RacingPlugin,
}

__all__ = [
    'GamePlugin',
    'GomokuPlugin', 
    'Shooter2DPlugin',
    'WerewolfPlugin',
    'MonopolyPlugin', 
    'RacingPlugin',
    'GAME_PLUGINS'
]
