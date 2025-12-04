"""
五子棋游戏实现
"""
from typing import Any, Dict, List, Optional, Tuple
from ..base import (
    GamePlugin, GameContext, RoomState, NetworkEvent,
    GameState, EventType
)


class GomokuPlugin(GamePlugin):
    """五子棋游戏插件"""
    
    PLUGIN_NAME = "gomoku"
    PLUGIN_VERSION = "0.1.0"
    PLUGIN_DESCRIPTION = "经典五子棋对战"
    MIN_PLAYERS = 2
    MAX_PLAYERS = 2
    SUPPORTS_SPECTATE = True
    
    # 棋盘大小
    BOARD_SIZE = 15
    
    def __init__(self):
        super().__init__()
        self._board: List[List[int]] = []  # 0=空, 1=黑, 2=白
        self._current_player: int = 1       # 当前玩家 (1=黑, 2=白)
        self._my_color: int = 0             # 我方颜色
        self._winner: int = 0               # 获胜者
        self._history: List[Tuple[int, int, int]] = []  # 落子历史
        self._last_move: Optional[Tuple[int, int]] = None
    
    def load(self, context: GameContext) -> bool:
        """加载游戏资源"""
        self._context = context
        self._state = GameState.LOADING
        
        # 初始化棋盘
        self._reset_board()
        
        self._state = GameState.READY
        self._is_loaded = True
        return True
    
    def _reset_board(self) -> None:
        """重置棋盘"""
        self._board = [[0] * self.BOARD_SIZE for _ in range(self.BOARD_SIZE)]
        self._current_player = 1
        self._winner = 0
        self._history.clear()
        self._last_move = None
    
    def join_room(self, room_state: RoomState) -> bool:
        """加入房间"""
        self._room_state = room_state
        
        # 确定我方颜色（先加入的玩家为黑方）
        if self._context and self._context.local_user:
            for i, player in enumerate(room_state.current_players):
                if player.user_id == self._context.local_user.user_id:
                    self._my_color = 1 if i == 0 else 2
                    break
        
        return True
    
    def start_game(self) -> bool:
        """开始游戏"""
        self._reset_board()
        self._state = GameState.PLAYING
        return True
    
    def dispose(self) -> None:
        """清理资源"""
        self._board.clear()
        self._history.clear()
        self._state = GameState.IDLE
        self._is_loaded = False
    
    def update(self, dt: float) -> None:
        """游戏更新"""
        pass  # 五子棋是回合制，不需要实时更新
    
    def render(self, surface: Any) -> None:
        """渲染棋盘（由 UI 层调用）"""
        # 返回当前游戏状态供 UI 层渲染
        pass
    
    def on_network(self, event: NetworkEvent) -> None:
        """处理网络事件"""
        if event.type == EventType.STATE:
            payload = event.payload
            
            if payload.get("action") == "move":
                row = payload.get("row", 0)
                col = payload.get("col", 0)
                player = payload.get("player", 0)
                self._apply_move(row, col, player)
            
            elif payload.get("action") == "game_over":
                self._winner = payload.get("winner", 0)
                self._state = GameState.FINISHED
            
            elif payload.get("action") == "reset":
                self._reset_board()
                self._state = GameState.PLAYING
    
    def _apply_move(self, row: int, col: int, player: int) -> None:
        """应用落子"""
        if 0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE:
            if self._board[row][col] == 0:
                self._board[row][col] = player
                self._history.append((row, col, player))
                self._last_move = (row, col)
                self._current_player = 3 - player  # 切换玩家
    
    def place_stone(self, row: int, col: int) -> bool:
        """
        尝试落子
        
        Args:
            row: 行
            col: 列
            
        Returns:
            是否成功（本地验证）
        """
        # 检查游戏状态
        if self._state != GameState.PLAYING:
            return False
        
        # 检查是否轮到我
        if self._current_player != self._my_color:
            return False
        
        # 检查位置是否合法
        if not (0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE):
            return False
        
        if self._board[row][col] != 0:
            return False
        
        # 发送落子请求到服务器
        self.send_input({
            "action": "move",
            "row": row,
            "col": col
        })
        
        return True
    
    def on_mouse_down(self, button: int, x: int, y: int) -> None:
        """处理鼠标点击"""
        if button == 1:  # 左键
            # 将屏幕坐标转换为棋盘坐标（由 UI 层实现）
            pass
    
    def get_board_state(self) -> Dict[str, Any]:
        """获取棋盘状态供 UI 层使用"""
        return {
            "board": self._board,
            "current_player": self._current_player,
            "my_color": self._my_color,
            "winner": self._winner,
            "last_move": self._last_move,
            "history_count": len(self._history)
        }
    
    def get_history(self) -> List[Tuple[int, int, int]]:
        """获取落子历史"""
        return self._history.copy()
    
    def is_my_turn(self) -> bool:
        """是否轮到我"""
        return self._current_player == self._my_color and self._state == GameState.PLAYING

