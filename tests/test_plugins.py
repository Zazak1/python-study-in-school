"""
游戏插件测试
"""
import pytest
from client.plugins.base import (
    GamePlugin, GameContext, RoomState, NetworkEvent,
    GameState, EventType, PlayerInfo
)
from client.plugins.gomoku.game import GomokuPlugin
from client.plugins.shooter2d.game import Shooter2DPlugin
from client.plugins.monopoly.game import MonopolyPlugin
from client.plugins.werewolf.game import WerewolfPlugin
from client.plugins.racing.game import RacingPlugin


class TestGomokuPlugin:
    """五子棋插件测试"""
    
    @pytest.fixture
    def plugin(self):
        return GomokuPlugin()
    
    @pytest.fixture
    def context(self):
        return GameContext(
            assets_path="/tmp/assets",
            cache_path="/tmp/cache",
            local_user=PlayerInfo(
                user_id="test_user",
                nickname="测试玩家"
            )
        )
    
    def test_plugin_info(self, plugin):
        """测试插件信息"""
        assert plugin.PLUGIN_NAME == "gomoku"
        assert plugin.MIN_PLAYERS == 2
        assert plugin.MAX_PLAYERS == 2
    
    def test_load(self, plugin, context):
        """测试加载"""
        result = plugin.load(context)
        assert result is True
        assert plugin.state == GameState.READY
    
    def test_board_initialization(self, plugin, context):
        """测试棋盘初始化"""
        plugin.load(context)
        
        board_state = plugin.get_board_state()
        assert len(board_state["board"]) == 15
        assert len(board_state["board"][0]) == 15
        assert board_state["current_player"] == 1
    
    def test_join_room(self, plugin, context):
        """测试加入房间"""
        plugin.load(context)
        
        room_state = RoomState(
            room_id="test_room",
            game_type="gomoku",
            max_players=2,
            current_players=[
                PlayerInfo(user_id="test_user", nickname="玩家1"),
                PlayerInfo(user_id="other_user", nickname="玩家2")
            ]
        )
        
        result = plugin.join_room(room_state)
        assert result is True
        assert plugin._my_color == 1  # 第一个加入的是黑方


class TestShooter2DPlugin:
    """2D 射击插件测试"""
    
    @pytest.fixture
    def plugin(self):
        return Shooter2DPlugin()
    
    @pytest.fixture
    def context(self):
        return GameContext(
            assets_path="/tmp/assets",
            cache_path="/tmp/cache",
            local_user=PlayerInfo(
                user_id="test_user",
                nickname="测试玩家"
            )
        )
    
    def test_plugin_info(self, plugin):
        """测试插件信息"""
        assert plugin.PLUGIN_NAME == "shooter2d"
        assert plugin.MIN_PLAYERS == 2
        assert plugin.MAX_PLAYERS == 8
    
    def test_load(self, plugin, context):
        """测试加载"""
        result = plugin.load(context)
        assert result is True
        assert plugin.state == GameState.READY
    
    def test_input_handling(self, plugin, context):
        """测试输入处理"""
        plugin.load(context)
        
        plugin.on_key_down("W")
        assert "w" in plugin._keys_pressed
        
        plugin.on_key_up("W")
        assert "w" not in plugin._keys_pressed
    
    def test_mouse_tracking(self, plugin, context):
        """测试鼠标追踪"""
        plugin.load(context)
        
        plugin.on_mouse_move(100, 200)
        assert plugin._mouse_position.x == 100
        assert plugin._mouse_position.y == 200


class TestMonopolyPlugin:
    """大富翁插件测试"""

    @pytest.fixture
    def plugin(self):
        return MonopolyPlugin()

    @pytest.fixture
    def events(self):
        return []

    @pytest.fixture
    def context(self, events):
        def send_network(ev):
            events.append(ev)

        return GameContext(
            assets_path="/tmp/assets",
            cache_path="/tmp/cache",
            local_user=PlayerInfo(user_id="test_user", nickname="测试玩家"),
            send_network=send_network,
        )

    def test_load(self, plugin, context):
        assert plugin.load(context) is True
        assert plugin.state == GameState.READY

    def test_roll_buy_end_turn_flow(self, plugin, context, events):
        plugin.load(context)
        room_state = RoomState(
            room_id="room1",
            game_type="monopoly",
            max_players=4,
            current_players=[
                PlayerInfo(user_id="test_user", nickname="玩家1"),
                PlayerInfo(user_id="other_user", nickname="玩家2"),
            ],
        )
        plugin.join_room(room_state)
        plugin.start_game()

        tiles = [
            {"id": 0, "type": "start", "name": "起点"},
            {"id": 1, "type": "property", "name": "地中海大道", "price": 100, "rent": [10], "owner": None},
        ]
        players = [
            {"user_id": "test_user", "position": 1, "money": 150, "bankrupt": False, "properties": []},
            {"user_id": "other_user", "position": 0, "money": 150, "bankrupt": False, "properties": []},
        ]

        plugin.on_network(
            NetworkEvent(
                type=EventType.STATE,
                payload={
                    "action": "game_start",
                    "phase": "rolling",
                    "current_player": "test_user",
                    "tiles": tiles,
                    "players": players,
                },
            )
        )
        assert plugin.is_my_turn() is True

        plugin.roll_dice()
        assert events[-1].type == EventType.INPUT
        assert events[-1].payload.get("action") == "roll_dice"

        plugin.on_network(
            NetworkEvent(
                type=EventType.STATE,
                payload={
                    "action": "player_move",
                    "user_id": "test_user",
                    "position": 1,
                    "dice": [1, 0],
                    "players": players,
                },
            )
        )

        plugin.buy_property()
        assert events[-1].payload.get("action") == "buy_property"

        plugin.on_network(
            NetworkEvent(
                type=EventType.STATE,
                payload={"action": "buy_property", "user_id": "test_user", "tile_id": 1, "money": 50},
            )
        )

        state = plugin.render(None)
        assert state["tiles"][1]["owner"] == "test_user"
        assert state["players"]["test_user"]["money"] == 50

        plugin.end_turn()
        assert events[-1].payload.get("action") == "end_turn"

    def test_player_disconnected_applies_server_state(self, plugin, context):
        plugin.load(context)
        room_state = RoomState(
            room_id="room1",
            game_type="monopoly",
            max_players=4,
            current_players=[
                PlayerInfo(user_id="test_user", nickname="玩家1"),
                PlayerInfo(user_id="other_user", nickname="玩家2"),
            ],
        )
        plugin.join_room(room_state)
        plugin.start_game()

        tiles = [
            {"id": 0, "type": "start", "name": "起点", "owner": None},
            {"id": 1, "type": "property", "name": "地中海大道", "price": 100, "rent": [10], "owner": None},
        ]
        players = [
            {"user_id": "test_user", "position": 1, "money": 0, "bankrupt": True, "properties": []},
            {"user_id": "other_user", "position": 0, "money": 150, "bankrupt": False, "properties": []},
        ]

        plugin.on_network(
            NetworkEvent(
                type=EventType.STATE,
                payload={
                    "action": "player_disconnected",
                    "user_id": "test_user",
                    "phase": "rolling",
                    "current_player": "other_user",
                    "tiles": tiles,
                    "players": players,
                },
            )
        )

        state = plugin.render(None)
        assert state["current_player"] == "other_user"
        assert state["players"]["test_user"]["bankrupt"] is True
        assert state["tiles"][1]["owner"] is None


class TestWerewolfPlugin:
    """狼人杀插件测试"""

    @pytest.fixture
    def plugin(self):
        return WerewolfPlugin()

    @pytest.fixture
    def events(self):
        return []

    @pytest.fixture
    def context(self, events):
        def send_network(ev):
            events.append(ev)

        return GameContext(
            assets_path="/tmp/assets",
            cache_path="/tmp/cache",
            local_user=PlayerInfo(user_id="test_user", nickname="测试玩家"),
            send_network=send_network,
        )

    def test_role_and_actions(self, plugin, context, events):
        plugin.load(context)
        room_state = RoomState(
            room_id="room1",
            game_type="werewolf",
            max_players=12,
            current_players=[PlayerInfo(user_id=f"u{i}", nickname=f"p{i}") for i in range(6)]
            + [PlayerInfo(user_id="test_user", nickname="me")],
        )
        plugin.join_room(room_state)
        plugin.start_game()

        plugin.on_network(
            NetworkEvent(
                type=EventType.STATE,
                payload={
                    "action": "game_start",
                    "phase": "night",
                    "day": 0,
                    "timer": 20,
                    "players": [{"user_id": p.user_id, "alive": True} for p in room_state.current_players],
                },
            )
        )

        # 预言家：查验
        plugin.on_network(NetworkEvent(type=EventType.SYSTEM, payload={"action": "role", "role": "seer"}))
        plugin.seer_check("u1")
        assert events[-1].payload.get("action") == "seer_check"
        assert events[-1].payload.get("target") == "u1"

        plugin.on_network(
            NetworkEvent(type=EventType.SYSTEM, payload={"action": "seer_result", "target": "u1", "is_wolf": False})
        )
        assert plugin.render(None)["seer_result"]["target"] == "u1"

        # 白天不能击杀
        before = len(events)
        plugin.wolf_kill("u2")
        assert len(events) == before

        # 投票
        plugin.on_network(NetworkEvent(type=EventType.SYNC, payload={"phase": "vote", "timer": 15}))
        plugin.vote("u2")
        assert events[-1].payload.get("action") == "vote"
        assert events[-1].payload.get("target") == "u2"


class TestRacingPlugin:
    """赛车插件测试"""

    @pytest.fixture
    def plugin(self):
        return RacingPlugin()

    @pytest.fixture
    def events(self):
        return []

    @pytest.fixture
    def context(self, events):
        def send_network(ev):
            events.append(ev)

        return GameContext(
            assets_path="/tmp/assets",
            cache_path="/tmp/cache",
            local_user=PlayerInfo(user_id="test_user", nickname="测试玩家"),
            send_network=send_network,
        )

    def test_input_clamp_and_state(self, plugin, context, events):
        plugin.load(context)
        room_state = RoomState(
            room_id="room1",
            game_type="racing",
            max_players=6,
            current_players=[
                PlayerInfo(user_id="test_user", nickname="me"),
                PlayerInfo(user_id="other_user", nickname="other"),
            ],
        )
        plugin.join_room(room_state)
        plugin.start_game()

        plugin.on_network(
            NetworkEvent(
                type=EventType.STATE,
                payload={
                    "action": "game_start",
                    "state": "countdown",
                    "countdown": 3,
                    "track": {"name": "default", "checkpoints": [(0, 0, 0), (50, 0, 0)]},
                    "cars": [
                        {
                            "user_id": "test_user",
                            "nickname": "me",
                            "pos": {"x": 0.0, "y": 0.0, "z": 0.0},
                            "vel": {"x": 0.0, "y": 0.0, "z": 0.0},
                            "rotation": 0.0,
                            "lap": 0,
                            "checkpoint": 0,
                            "rank": 0,
                            "finished": False,
                        }
                    ],
                },
            )
        )

        plugin.set_input(throttle=1.2, brake=-0.5, steering=2.0)
        assert events[-1].payload.get("action") == "game_input"
        assert events[-1].payload.get("throttle") == 1.0
        assert events[-1].payload.get("brake") == 0.0
        assert events[-1].payload.get("steering") == 1.0
