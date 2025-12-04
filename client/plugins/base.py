"""
GamePlugin 基础抽象类
定义游戏插件的生命周期、场景管理、输入/网络回调接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum, auto


class GameState(Enum):
    """游戏状态枚举"""
    IDLE = auto()           # 空闲
    LOADING = auto()        # 加载中
    READY = auto()          # 准备就绪
    PLAYING = auto()        # 游戏中
    PAUSED = auto()         # 暂停
    FINISHED = auto()       # 已结束
    ERROR = auto()          # 错误


class EventType(Enum):
    """网络事件类型"""
    INPUT = auto()          # 输入事件
    STATE = auto()          # 状态更新
    CHAT = auto()           # 聊天消息
    SYSTEM = auto()         # 系统消息
    SYNC = auto()           # 帧同步
    RECONCILE = auto()      # 状态纠正


@dataclass
class NetworkEvent:
    """网络事件数据结构"""
    type: EventType
    payload: Dict[str, Any]
    frame_id: int = 0
    event_id: str = ""
    timestamp: float = 0.0
    sender_id: Optional[str] = None


@dataclass
class PlayerInfo:
    """玩家信息"""
    user_id: str
    nickname: str
    avatar_url: str = ""
    team_id: Optional[int] = None
    is_ready: bool = False
    is_host: bool = False


@dataclass
class RoomState:
    """房间状态"""
    room_id: str
    game_type: str
    max_players: int
    current_players: List[PlayerInfo] = field(default_factory=list)
    host_id: str = ""
    tick_rate: int = 20      # 帧率
    rules: Dict[str, Any] = field(default_factory=dict)
    allow_spectate: bool = True
    random_seed: int = 0


@dataclass
class GameContext:
    """游戏上下文，由宿主传入插件"""
    # 资源路径
    assets_path: str
    cache_path: str
    
    # 用户信息
    local_user: PlayerInfo = None
    
    # 回调函数
    send_network: Callable[[NetworkEvent], None] = None
    request_render: Callable[[], None] = None
    play_sound: Callable[[str], None] = None
    show_notification: Callable[[str, str], None] = None
    
    # 配置
    config: Dict[str, Any] = field(default_factory=dict)


class GamePlugin(ABC):
    """
    游戏插件抽象基类
    
    所有游戏模块必须继承此类并实现相应方法
    """
    
    # 插件元信息（子类需覆盖）
    PLUGIN_NAME: str = "base"
    PLUGIN_VERSION: str = "0.0.1"
    PLUGIN_DESCRIPTION: str = ""
    MIN_PLAYERS: int = 1
    MAX_PLAYERS: int = 8
    SUPPORTS_SPECTATE: bool = True
    
    def __init__(self):
        self._state: GameState = GameState.IDLE
        self._context: Optional[GameContext] = None
        self._room_state: Optional[RoomState] = None
        self._frame_id: int = 0
        self._is_loaded: bool = False
    
    @property
    def state(self) -> GameState:
        """获取当前游戏状态"""
        return self._state
    
    @property
    def context(self) -> Optional[GameContext]:
        """获取游戏上下文"""
        return self._context
    
    @property
    def room_state(self) -> Optional[RoomState]:
        """获取房间状态"""
        return self._room_state
    
    @property
    def frame_id(self) -> int:
        """获取当前帧号"""
        return self._frame_id
    
    # ==================== 生命周期方法 ====================
    
    @abstractmethod
    def load(self, context: GameContext) -> bool:
        """
        加载资源、注册输入映射、初始化场景
        
        Args:
            context: 游戏上下文，包含资源路径和回调函数
            
        Returns:
            是否加载成功
        """
        pass
    
    @abstractmethod
    def join_room(self, room_state: RoomState) -> bool:
        """
        根据服务器房间信息进入对局
        
        Args:
            room_state: 房间状态信息
            
        Returns:
            是否成功加入
        """
        pass
    
    @abstractmethod
    def start_game(self) -> bool:
        """
        开始游戏
        
        Returns:
            是否成功开始
        """
        pass
    
    @abstractmethod
    def dispose(self) -> None:
        """
        释放纹理/音频，回收线程/协程
        清理所有资源
        """
        pass
    
    # ==================== 游戏循环方法 ====================
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        客户端帧循环
        
        可在此做客户端预测与插值
        
        Args:
            dt: 距上一帧的时间间隔（秒）
        """
        pass
    
    @abstractmethod
    def render(self, surface: Any) -> None:
        """
        渲染当前帧
        
        Args:
            surface: 由宿主传入的渲染 surface/窗口句柄
        """
        pass
    
    # ==================== 网络方法 ====================
    
    @abstractmethod
    def on_network(self, event: NetworkEvent) -> None:
        """
        处理来自服务器的帧同步/状态更新
        
        Args:
            event: 网络事件
        """
        pass
    
    def send_input(self, input_data: Dict[str, Any]) -> None:
        """
        发送玩家输入到服务器
        
        Args:
            input_data: 输入数据
        """
        if self._context and self._context.send_network:
            event = NetworkEvent(
                type=EventType.INPUT,
                payload=input_data,
                frame_id=self._frame_id
            )
            self._context.send_network(event)
    
    # ==================== 输入处理方法 ====================
    
    def on_key_down(self, key: str) -> None:
        """键盘按下事件"""
        pass
    
    def on_key_up(self, key: str) -> None:
        """键盘释放事件"""
        pass
    
    def on_mouse_move(self, x: int, y: int) -> None:
        """鼠标移动事件"""
        pass
    
    def on_mouse_down(self, button: int, x: int, y: int) -> None:
        """鼠标按下事件"""
        pass
    
    def on_mouse_up(self, button: int, x: int, y: int) -> None:
        """鼠标释放事件"""
        pass
    
    # ==================== 辅助方法 ====================
    
    def pause(self) -> None:
        """暂停游戏"""
        if self._state == GameState.PLAYING:
            self._state = GameState.PAUSED
    
    def resume(self) -> None:
        """恢复游戏"""
        if self._state == GameState.PAUSED:
            self._state = GameState.PLAYING
    
    def get_game_info(self) -> Dict[str, Any]:
        """获取游戏信息"""
        return {
            "name": self.PLUGIN_NAME,
            "version": self.PLUGIN_VERSION,
            "description": self.PLUGIN_DESCRIPTION,
            "min_players": self.MIN_PLAYERS,
            "max_players": self.MAX_PLAYERS,
            "supports_spectate": self.SUPPORTS_SPECTATE,
            "state": self._state.name
        }

