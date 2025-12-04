"""
狼人杀游戏插件
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum, auto

from ..base import GamePlugin


class GamePhase(Enum):
    """游戏阶段"""
    WAITING = auto()     # 等待
    DEAL_CARDS = auto()  # 发牌
    NIGHT = auto()       # 夜晚
    DAY_DISCUSS = auto() # 白天讨论
    DAY_VOTE = auto()    # 白天投票
    EXILE = auto()       # 放逐
    GAME_OVER = auto()   # 结束


class Role(Enum):
    """角色"""
    VILLAGER = "村民"
    WEREWOLF = "狼人"
    SEER = "预言家"
    WITCH = "女巫"
    HUNTER = "猎人"
    GUARD = "守卫"
    IDIOT = "白痴"


@dataclass
class Player:
    """玩家"""
    user_id: str
    nickname: str
    role: Optional[Role] = None
    is_alive: bool = True
    is_protected: bool = False
    voted_for: Optional[str] = None  # 投票目标


@dataclass
class GameState:
    """游戏状态"""
    phase: GamePhase = GamePhase.WAITING
    day_count: int = 0
    players: Dict[str, Player] = field(default_factory=dict)
    timer: int = 0  # 当前阶段剩余时间
    
    # 夜晚行动
    wolf_target: Optional[str] = None
    seer_target: Optional[str] = None
    witch_save: bool = False
    witch_poison: Optional[str] = None
    guard_target: Optional[str] = None
    
    # 投票
    votes: Dict[str, str] = field(default_factory=dict)  # voter -> target


class WerewolfPlugin(GamePlugin):
    """狼人杀游戏插件"""
    
    GAME_TYPE = "werewolf"
    NAME = "狼人杀"
    VERSION = "0.1.0"
    
    # 阶段时长（秒）
    PHASE_TIMERS = {
        GamePhase.DEAL_CARDS: 10,
        GamePhase.NIGHT: 60,
        GamePhase.DAY_DISCUSS: 120,
        GamePhase.DAY_VOTE: 30,
        GamePhase.EXILE: 10,
    }
    
    def __init__(self):
        super().__init__()
        self.state = GameState()
        self.my_role: Optional[Role] = None
        
        # 回调
        self.on_phase_change = None
        self.on_player_update = None
        self.on_vote_result = None
    
    def get_game_info(self) -> Dict[str, Any]:
        return {
            "game_type": self.GAME_TYPE,
            "name": self.NAME,
            "version": self.VERSION,
            "description": "经典狼人杀，支持多种角色配置",
            "icon": "🐺",
            "color": "#8B5CF6",
            "min_players": 6,
            "max_players": 12,
            "features": ["语音聊天", "角色配置", "历史记录"]
        }
    
    def load(self, context: Dict[str, Any]):
        """加载游戏"""
        self._is_loaded = True
        
        # 加载角色图标等资源
        self.resources = context.get('resources', {})
    
    def join_room(self, room_state: Dict[str, Any]):
        """加入房间"""
        self._room_id = room_state.get('room_id')
        
        # 初始化玩家
        for p in room_state.get('players', []):
            self.state.players[p['user_id']] = Player(
                user_id=p['user_id'],
                nickname=p['nickname']
            )
    
    def on_network(self, event: Dict[str, Any]):
        """处理网络事件"""
        event_type = event.get('type')
        payload = event.get('payload', {})
        
        if event_type == 'phase_change':
            self._handle_phase_change(payload)
        
        elif event_type == 'deal_role':
            # 收到自己的角色
            role_name = payload.get('role')
            self.my_role = Role(role_name)
        
        elif event_type == 'night_result':
            # 夜晚结果
            self._handle_night_result(payload)
        
        elif event_type == 'vote_update':
            # 投票更新
            self._handle_vote_update(payload)
        
        elif event_type == 'player_death':
            # 玩家死亡
            user_id = payload.get('user_id')
            if user_id in self.state.players:
                self.state.players[user_id].is_alive = False
        
        elif event_type == 'game_over':
            # 游戏结束
            self.state.phase = GamePhase.GAME_OVER
    
    def _handle_phase_change(self, payload: Dict):
        """处理阶段变化"""
        phase_name = payload.get('phase')
        self.state.phase = GamePhase[phase_name]
        self.state.timer = self.PHASE_TIMERS.get(self.state.phase, 0)
        
        if self.state.phase == GamePhase.DAY_DISCUSS:
            self.state.day_count += 1
        
        # 重置夜晚行动
        if self.state.phase == GamePhase.NIGHT:
            self.state.wolf_target = None
            self.state.seer_target = None
            self.state.witch_save = False
            self.state.witch_poison = None
            self.state.guard_target = None
        
        # 重置投票
        if self.state.phase == GamePhase.DAY_VOTE:
            self.state.votes.clear()
        
        if self.on_phase_change:
            self.on_phase_change(self.state.phase)
    
    def _handle_night_result(self, payload: Dict):
        """处理夜晚结果"""
        # 预言家查验结果
        if 'seer_result' in payload and self.my_role == Role.SEER:
            # 显示查验结果
            pass
        
        # 死亡玩家
        for user_id in payload.get('deaths', []):
            if user_id in self.state.players:
                self.state.players[user_id].is_alive = False
    
    def _handle_vote_update(self, payload: Dict):
        """处理投票更新"""
        voter = payload.get('voter')
        target = payload.get('target')
        
        if voter and target:
            self.state.votes[voter] = target
    
    def update(self, dt: float):
        """更新"""
        # 更新计时器
        if self.state.timer > 0:
            self.state.timer -= dt
    
    def render(self, surface):
        """渲染（由 UI 层处理）"""
        pass
    
    def dispose(self):
        """释放资源"""
        self._is_loaded = False
        self.state = GameState()
    
    # ========== 游戏操作 ==========
    
    def send_wolf_action(self, target_id: str):
        """狼人行动 - 选择击杀目标"""
        if self.my_role != Role.WEREWOLF:
            return
        
        self._send_action('wolf_kill', {'target': target_id})
    
    def send_seer_action(self, target_id: str):
        """预言家行动 - 查验玩家"""
        if self.my_role != Role.SEER:
            return
        
        self._send_action('seer_check', {'target': target_id})
    
    def send_witch_save(self):
        """女巫行动 - 救人"""
        if self.my_role != Role.WITCH:
            return
        
        self._send_action('witch_save', {})
    
    def send_witch_poison(self, target_id: str):
        """女巫行动 - 毒杀"""
        if self.my_role != Role.WITCH:
            return
        
        self._send_action('witch_poison', {'target': target_id})
    
    def send_guard_protect(self, target_id: str):
        """守卫行动 - 保护"""
        if self.my_role != Role.GUARD:
            return
        
        self._send_action('guard_protect', {'target': target_id})
    
    def send_vote(self, target_id: str):
        """投票"""
        self._send_action('vote', {'target': target_id})
    
    def _send_action(self, action: str, data: Dict):
        """发送行动"""
        # 通过网络发送
        if self._network_callback:
            self._network_callback({
                'type': 'game_action',
                'action': action,
                'room_id': self._room_id,
                **data
            })
    
    # ========== 查询方法 ==========
    
    def get_alive_players(self) -> List[Player]:
        """获取存活玩家"""
        return [p for p in self.state.players.values() if p.is_alive]
    
    def get_vote_count(self) -> Dict[str, int]:
        """获取投票统计"""
        counts = {}
        for target in self.state.votes.values():
            counts[target] = counts.get(target, 0) + 1
        return counts
    
    def can_act(self) -> bool:
        """当前是否可以行动"""
        if not self.my_role:
            return False
        
        phase = self.state.phase
        
        if phase == GamePhase.NIGHT:
            return self.my_role in [
                Role.WEREWOLF, Role.SEER, Role.WITCH, Role.GUARD
            ]
        
        if phase == GamePhase.DAY_VOTE:
            return True
        
        return False

