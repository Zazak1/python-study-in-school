"""
大富翁游戏插件
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum, auto

from ..base import GamePlugin


class TileType(Enum):
    """地块类型"""
    START = "起点"
    PROPERTY = "地产"
    CHANCE = "机会"
    CHEST = "宝箱"
    TAX = "税收"
    JAIL = "监狱"
    STATION = "车站"
    UTILITY = "公共设施"


@dataclass
class Tile:
    """地块"""
    id: int
    type: TileType
    name: str
    price: int = 0
    rent: List[int] = field(default_factory=list)  # 不同等级的租金
    owner_id: Optional[str] = None
    level: int = 0  # 升级等级
    color_group: str = ""


@dataclass
class PlayerState:
    """玩家状态"""
    user_id: str
    nickname: str
    position: int = 0  # 当前位置
    money: int = 15000  # 金钱
    properties: List[int] = field(default_factory=list)  # 拥有的地产
    in_jail: bool = False
    jail_turns: int = 0
    is_bankrupt: bool = False


@dataclass
class GameState:
    """游戏状态"""
    players: Dict[str, PlayerState] = field(default_factory=dict)
    tiles: List[Tile] = field(default_factory=list)
    current_turn: int = 0  # 当前回合
    current_player: str = ""  # 当前玩家
    dice: tuple = (0, 0)  # 骰子点数
    phase: str = "waiting"  # waiting / rolling / moving / action / end


class MonopolyPlugin(GamePlugin):
    """大富翁游戏插件"""
    
    GAME_TYPE = "monopoly"
    NAME = "大富翁"
    VERSION = "0.1.0"
    
    # 默认地图
    DEFAULT_MAP = [
        {"type": TileType.START, "name": "起点"},
        {"type": TileType.PROPERTY, "name": "地中海大道", "price": 600, "rent": [20, 100, 300, 900, 1600], "color": "brown"},
        {"type": TileType.CHEST, "name": "宝箱"},
        {"type": TileType.PROPERTY, "name": "波罗的海大道", "price": 600, "rent": [40, 200, 600, 1800, 3200], "color": "brown"},
        {"type": TileType.TAX, "name": "所得税"},
        {"type": TileType.STATION, "name": "火车站", "price": 2000, "rent": [250, 500, 1000, 2000]},
        {"type": TileType.PROPERTY, "name": "东方大道", "price": 1000, "rent": [60, 300, 900, 2700, 4000], "color": "lightblue"},
        {"type": TileType.CHANCE, "name": "机会"},
        {"type": TileType.PROPERTY, "name": "佛蒙特大道", "price": 1000, "rent": [60, 300, 900, 2700, 4000], "color": "lightblue"},
        {"type": TileType.PROPERTY, "name": "康涅狄格大道", "price": 1200, "rent": [80, 400, 1000, 3000, 4500], "color": "lightblue"},
        {"type": TileType.JAIL, "name": "监狱"},
        # ... 更多地块
    ]
    
    def __init__(self):
        super().__init__()
        self.state = GameState()
        self.my_user_id: Optional[str] = None
        
        # 回调
        self.on_dice_roll = None
        self.on_move = None
        self.on_buy_property = None
        self.on_pay_rent = None
        self.on_turn_change = None
    
    def get_game_info(self) -> Dict[str, Any]:
        return {
            "game_type": self.GAME_TYPE,
            "name": self.NAME,
            "version": self.VERSION,
            "description": "经典大富翁，买地建房收租金",
            "icon": "🎲",
            "color": "#F59E0B",
            "min_players": 2,
            "max_players": 4,
            "features": ["多地图", "道具卡", "联机对战"]
        }
    
    def load(self, context: Dict[str, Any]):
        """加载游戏"""
        self._is_loaded = True
        self.my_user_id = context.get('user_id')
        
        # 初始化地图
        self._init_map()
    
    def _init_map(self):
        """初始化地图"""
        self.state.tiles = []
        for i, tile_data in enumerate(self.DEFAULT_MAP):
            tile = Tile(
                id=i,
                type=tile_data["type"],
                name=tile_data["name"],
                price=tile_data.get("price", 0),
                rent=tile_data.get("rent", []),
                color_group=tile_data.get("color", "")
            )
            self.state.tiles.append(tile)
    
    def join_room(self, room_state: Dict[str, Any]):
        """加入房间"""
        self._room_id = room_state.get('room_id')
        
        # 初始化玩家
        for p in room_state.get('players', []):
            self.state.players[p['user_id']] = PlayerState(
                user_id=p['user_id'],
                nickname=p['nickname']
            )
    
    def on_network(self, event: Dict[str, Any]):
        """处理网络事件"""
        event_type = event.get('type')
        payload = event.get('payload', {})
        
        if event_type == 'game_start':
            self.state.phase = "rolling"
            self.state.current_player = payload.get('first_player')
        
        elif event_type == 'dice_roll':
            self.state.dice = (payload['dice1'], payload['dice2'])
            if self.on_dice_roll:
                self.on_dice_roll(self.state.dice)
        
        elif event_type == 'player_move':
            user_id = payload['user_id']
            new_pos = payload['position']
            if user_id in self.state.players:
                self.state.players[user_id].position = new_pos
            if self.on_move:
                self.on_move(user_id, new_pos)
        
        elif event_type == 'buy_property':
            user_id = payload['user_id']
            tile_id = payload['tile_id']
            self._handle_buy_property(user_id, tile_id)
        
        elif event_type == 'pay_rent':
            payer_id = payload['payer']
            owner_id = payload['owner']
            amount = payload['amount']
            self._handle_pay_rent(payer_id, owner_id, amount)
        
        elif event_type == 'turn_end':
            self._next_turn(payload.get('next_player'))
        
        elif event_type == 'game_over':
            self.state.phase = "end"
    
    def _handle_buy_property(self, user_id: str, tile_id: int):
        """处理购买地产"""
        if tile_id < len(self.state.tiles):
            tile = self.state.tiles[tile_id]
            tile.owner_id = user_id
            
            if user_id in self.state.players:
                self.state.players[user_id].properties.append(tile_id)
                self.state.players[user_id].money -= tile.price
        
        if self.on_buy_property:
            self.on_buy_property(user_id, tile_id)
    
    def _handle_pay_rent(self, payer_id: str, owner_id: str, amount: int):
        """处理支付租金"""
        if payer_id in self.state.players:
            self.state.players[payer_id].money -= amount
        if owner_id in self.state.players:
            self.state.players[owner_id].money += amount
        
        if self.on_pay_rent:
            self.on_pay_rent(payer_id, owner_id, amount)
    
    def _next_turn(self, next_player: str):
        """下一回合"""
        self.state.current_turn += 1
        self.state.current_player = next_player
        self.state.phase = "rolling"
        
        if self.on_turn_change:
            self.on_turn_change(next_player)
    
    def update(self, dt: float):
        """更新"""
        pass
    
    def render(self, surface):
        """渲染（由 UI 层处理）"""
        pass
    
    def dispose(self):
        """释放资源"""
        self._is_loaded = False
        self.state = GameState()
    
    # ========== 游戏操作 ==========
    
    def roll_dice(self):
        """掷骰子"""
        if not self._is_my_turn():
            return
        
        self._send_action('roll_dice', {})
    
    def buy_property(self):
        """购买当前位置的地产"""
        if not self._is_my_turn():
            return
        
        player = self.state.players.get(self.my_user_id)
        if not player:
            return
        
        tile = self.state.tiles[player.position]
        if tile.type == TileType.PROPERTY and tile.owner_id is None:
            if player.money >= tile.price:
                self._send_action('buy_property', {'tile_id': tile.id})
    
    def end_turn(self):
        """结束回合"""
        if not self._is_my_turn():
            return
        
        self._send_action('end_turn', {})
    
    def _is_my_turn(self) -> bool:
        """是否是我的回合"""
        return self.state.current_player == self.my_user_id
    
    def _send_action(self, action: str, data: Dict):
        """发送行动"""
        if self._network_callback:
            self._network_callback({
                'type': 'game_action',
                'action': action,
                'room_id': self._room_id,
                **data
            })
    
    # ========== 查询方法 ==========
    
    def get_my_state(self) -> Optional[PlayerState]:
        """获取我的状态"""
        return self.state.players.get(self.my_user_id)
    
    def get_tile(self, position: int) -> Optional[Tile]:
        """获取地块"""
        if 0 <= position < len(self.state.tiles):
            return self.state.tiles[position]
        return None
    
    def get_property_owner(self, tile_id: int) -> Optional[str]:
        """获取地产拥有者"""
        tile = self.get_tile(tile_id)
        return tile.owner_id if tile else None
    
    def calculate_rent(self, tile_id: int) -> int:
        """计算租金"""
        tile = self.get_tile(tile_id)
        if not tile or not tile.owner_id:
            return 0
        
        if tile.level < len(tile.rent):
            return tile.rent[tile.level]
        return 0

