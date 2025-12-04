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

