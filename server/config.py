"""
服务器配置
"""
import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ServerConfig:
    """服务器配置"""
    
    # 基础配置
    host: str = "0.0.0.0"
    port: int = 8765
    debug: bool = True
    
    # WebSocket
    ws_path: str = "/ws"
    max_connections: int = 10000
    heartbeat_interval: int = 30  # 秒
    heartbeat_timeout: int = 90   # 秒
    
    # JWT 认证
    jwt_secret: str = "aether-party-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    # 房间
    max_rooms: int = 1000
    room_idle_timeout: int = 3600  # 空房间超时（秒）
    
    # 匹配
    match_timeout: int = 60  # 匹配超时（秒）
    match_check_interval: float = 1.0  # 匹配检查间隔
    
    # 游戏
    game_tick_rate: int = 20  # 帧率 (Hz)
    
    # 数据库（可选）
    db_url: str = "sqlite:///aether_party.db"
    
    @classmethod
    def from_env(cls) -> 'ServerConfig':
        """从环境变量加载配置"""
        return cls(
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "8765")),
            debug=os.getenv("DEBUG", "true").lower() == "true",
            jwt_secret=os.getenv("JWT_SECRET", cls.jwt_secret),
            db_url=os.getenv("DATABASE_URL", cls.db_url),
        )


# 全局配置实例
config = ServerConfig.from_env()


# 游戏配置
GAME_CONFIGS: Dict[str, Dict[str, Any]] = {
    'gomoku': {
        'name': '五子棋',
        'min_players': 2,
        'max_players': 2,
        'tick_rate': 0,  # 回合制，不需要 tick
        'sync_mode': 'event',  # 事件同步
    },
    'shooter2d': {
        'name': '2D 射击',
        'min_players': 2,
        'max_players': 8,
        'tick_rate': 20,
        'sync_mode': 'frame',  # 帧同步
    },
    'werewolf': {
        'name': '狼人杀',
        'min_players': 6,
        'max_players': 12,
        'tick_rate': 0,
        'sync_mode': 'state',  # 状态同步
    },
    'monopoly': {
        'name': '大富翁',
        'min_players': 2,
        'max_players': 4,
        'tick_rate': 0,
        'sync_mode': 'event',
    },
    'racing': {
        'name': '赛车竞速',
        'min_players': 2,
        'max_players': 6,
        'tick_rate': 30,
        'sync_mode': 'frame',
    },
}

