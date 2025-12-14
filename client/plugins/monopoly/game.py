"""
大富翁游戏插件（客户端）

与服务端 `server/games/monopoly.py` 的简化规则对齐：
- roll_dice -> player_move（含 dice/position/pay_rent/tax 等）
- buy_property
- end_turn
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..base import EventType, GameContext, GamePlugin, GameState, NetworkEvent, RoomState


@dataclass
class Tile:
    id: int
    type: str
    name: str
    price: int = 0
    rent: List[int] = field(default_factory=list)
    owner: Optional[str] = None


@dataclass
class PlayerState:
    user_id: str
    position: int = 0
    money: int = 15000
    bankrupt: bool = False
    properties: List[int] = field(default_factory=list)


class MonopolyPlugin(GamePlugin):
    """大富翁客户端插件（MVP：规则权威在服务器，客户端负责展示与发指令）"""

    PLUGIN_NAME = "monopoly"
    PLUGIN_VERSION = "0.1.0"
    PLUGIN_DESCRIPTION = "经典大富翁（MVP：服务器权威回合制）"
    MIN_PLAYERS = 2
    MAX_PLAYERS = 4
    SUPPORTS_SPECTATE = True

    def __init__(self):
        super().__init__()
        self._players: Dict[str, PlayerState] = {}
        self._tiles: List[Tile] = []
        self._phase: str = "waiting"
        self._current_player: str = ""
        self._dice: Tuple[int, int] = (0, 0)
        self._last_event: Dict[str, Any] = {}

        self._my_user_id: str = ""

    def load(self, context: GameContext) -> bool:
        self._context = context
        self._state = GameState.LOADING

        if context.local_user:
            self._my_user_id = context.local_user.user_id

        self._players.clear()
        self._tiles.clear()
        self._phase = "waiting"
        self._current_player = ""
        self._dice = (0, 0)
        self._last_event = {}

        self._state = GameState.READY
        self._is_loaded = True
        return True

    def join_room(self, room_state: RoomState) -> bool:
        self._room_state = room_state
        # 仅记录玩家列表，详细数值以服务器 game_start/game_sync 为准
        for p in room_state.current_players:
            self._players.setdefault(p.user_id, PlayerState(user_id=p.user_id))
        return True

    def start_game(self) -> bool:
        self._state = GameState.PLAYING
        return True

    def dispose(self) -> None:
        self._players.clear()
        self._tiles.clear()
        self._phase = "waiting"
        self._current_player = ""
        self._dice = (0, 0)
        self._last_event = {}
        self._state = GameState.IDLE
        self._is_loaded = False

    def update(self, dt: float) -> None:
        # 回合制；客户端无需帧更新
        return

    def render(self, surface: Any) -> Dict[str, Any]:
        return {
            "phase": self._phase,
            "current_player": self._current_player,
            "is_my_turn": self.is_my_turn(),
            "dice": self._dice,
            "players": {
                uid: {
                    "position": p.position,
                    "money": p.money,
                    "bankrupt": p.bankrupt,
                    "properties": p.properties,
                }
                for uid, p in self._players.items()
            },
            "tiles": [
                {
                    "id": t.id,
                    "type": t.type,
                    "name": t.name,
                    "owner": t.owner,
                    "price": t.price,
                    "rent": t.rent,
                }
                for t in self._tiles
            ],
            "last_event": self._last_event,
            "my_user_id": self._my_user_id,
        }

    def on_network(self, event: NetworkEvent) -> None:
        # game_sync（完整状态）
        if event.type == EventType.SYNC:
            state = event.payload or {}
            self._apply_full_state(state)
            return

        if event.type != EventType.STATE:
            return

        payload = event.payload or {}
        action = payload.get("action")
        if action == "game_start":
            self._apply_full_state(payload)
            return

        if action == "player_move":
            self._dice = tuple(payload.get("dice") or (0, 0))  # type: ignore[assignment]
            user_id = payload.get("user_id")
            if user_id and user_id in self._players:
                self._players[user_id].position = int(payload.get("position") or self._players[user_id].position)
            if isinstance(payload.get("players"), list):
                self._merge_players(payload.get("players"))
            if isinstance(payload.get("tiles"), list):
                # 租金/破产释放地产等会影响 tiles，直接用服务端状态覆盖
                self._tiles = [
                    Tile(
                        id=int(t.get("id") or 0),
                        type=str(t.get("type") or ""),
                        name=str(t.get("name") or ""),
                        owner=t.get("owner"),
                        price=int(t.get("price") or 0),
                        rent=list(t.get("rent") or []),
                    )
                    for t in payload.get("tiles") or []
                    if isinstance(t, dict)
                ]
            self._phase = "action"
            self._last_event = payload
            return

        if action == "player_disconnected":
            # 服务端可能在断线/主动离开时推进回合并释放地产
            self._apply_full_state(payload)
            self._last_event = payload
            if payload.get("game_over"):
                self._state = GameState.FINISHED
            return

        if action == "buy_property":
            user_id = payload.get("user_id")
            tile_id = payload.get("tile_id")
            if user_id and user_id in self._players and tile_id is not None:
                tile_id = int(tile_id)
                if 0 <= tile_id < len(self._tiles):
                    self._tiles[tile_id].owner = str(user_id)
                    self._players[user_id].money = int(payload.get("money") or self._players[user_id].money)
                    if tile_id not in self._players[user_id].properties:
                        self._players[user_id].properties.append(tile_id)
            if isinstance(payload.get("players"), list):
                self._merge_players(payload.get("players"))
            if isinstance(payload.get("tiles"), list):
                self._tiles = [
                    Tile(
                        id=int(t.get("id") or 0),
                        type=str(t.get("type") or ""),
                        name=str(t.get("name") or ""),
                        owner=t.get("owner"),
                        price=int(t.get("price") or 0),
                        rent=list(t.get("rent") or []),
                    )
                    for t in payload.get("tiles") or []
                    if isinstance(t, dict)
                ]
            self._phase = "end_turn"
            self._last_event = payload
            return

        if action == "turn_end":
            self._current_player = str(payload.get("next_player") or self._current_player)
            self._phase = str(payload.get("phase") or "rolling")
            self._last_event = payload
            return

        if action == "game_over":
            self._state = GameState.FINISHED
            self._last_event = payload

    # ========== 发送操作 ==========
    def is_my_turn(self) -> bool:
        return self._state == GameState.PLAYING and self._current_player == self._my_user_id

    def roll_dice(self):
        if not self.is_my_turn():
            return
        self.send_input({"action": "roll_dice"})

    def buy_property(self):
        if not self.is_my_turn():
            return
        self.send_input({"action": "buy_property"})

    def end_turn(self):
        if not self.is_my_turn():
            return
        self.send_input({"action": "end_turn"})

    # ========== 内部 ==========
    def _apply_full_state(self, state: Dict[str, Any]):
        self._phase = str(state.get("phase") or self._phase)
        self._current_player = str(state.get("current_player") or self._current_player)
        dice = state.get("dice")
        if isinstance(dice, (list, tuple)) and len(dice) == 2:
            self._dice = (int(dice[0]), int(dice[1]))

        tiles = state.get("tiles")
        if isinstance(tiles, list):
            self._tiles = [
                Tile(
                    id=int(t.get("id") or 0),
                    type=str(t.get("type") or ""),
                    name=str(t.get("name") or ""),
                    owner=t.get("owner"),
                    price=int(t.get("price") or 0),
                    rent=list(t.get("rent") or []),
                )
                for t in tiles
            ]

        players = state.get("players")
        if isinstance(players, list):
            self._merge_players(players)

    def _merge_players(self, players: list):
        for p in players:
            if not isinstance(p, dict):
                continue
            uid = p.get("user_id")
            if not uid:
                continue
            uid = str(uid)
            st = self._players.setdefault(uid, PlayerState(user_id=uid))
            st.position = int(p.get("position") or st.position)
            st.money = int(p.get("money") or st.money)
            st.bankrupt = bool(p.get("bankrupt") or False)
            if isinstance(p.get("properties"), list):
                st.properties = [int(x) for x in p.get("properties") if isinstance(x, int)]
