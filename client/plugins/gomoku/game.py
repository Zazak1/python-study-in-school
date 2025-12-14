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
        self._current_player = 1
        
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
        # 返回当前棋盘状态供 UI 层渲染（surface 由上层决定如何绘制）
        return self.get_board_state()
    
    def on_network(self, event: NetworkEvent) -> None:
        """处理网络事件"""
        if event.type == EventType.STATE:
            payload = event.payload

            action = payload.get("action")

            if action == "game_start":
                # 断线恢复或观战：服务端可能携带完整棋盘状态
                board = payload.get("board")
                if isinstance(board, list) and board and isinstance(board[0], list):
                    self._board = board

                player_colors = payload.get("player_colors")
                if isinstance(player_colors, dict):
                    # 服务端以 user_id -> 颜色（1/2）为准
                    if self._context and self._context.local_user:
                        self._my_color = int(player_colors.get(self._context.local_user.user_id, self._my_color) or self._my_color)

                    current_user = payload.get("current_player")
                    if current_user and current_user in player_colors:
                        self._current_player = int(player_colors.get(current_user) or self._current_player)

                history = payload.get("history")
                if isinstance(history, list):
                    try:
                        self._history = [tuple(x) for x in history]  # type: ignore[list-item]
                    except Exception:
                        pass
                    if self._history:
                        try:
                            last = self._history[-1]
                            self._last_move = (int(last[0]), int(last[1]))
                        except Exception:
                            pass

                winner = payload.get("winner")
                winner_color = payload.get("winner_color")
                if isinstance(winner_color, int):
                    self._winner = winner_color
                elif isinstance(winner, str) and isinstance(player_colors, dict):
                    try:
                        self._winner = int(player_colors.get(winner) or 0)
                    except Exception:
                        self._winner = 0

                if payload.get("is_finished") or payload.get("game_over"):
                    self._state = GameState.FINISHED
                else:
                    self._state = GameState.PLAYING
                return

            if action == "move":
                row = payload.get("row", 0)
                col = payload.get("col", 0)
                player = payload.get("player", 0)
                self._apply_move(row, col, player)
                
                # 服务端广播可能附带下一手
                next_player = payload.get("next_player")
                if next_player:
                    # 将 user_id 转换为颜色
                    color_map = {
                        p.user_id: (1 if i == 0 else 2)
                        for i, p in enumerate(self._room_state.current_players)
                    } if self._room_state else {}
                    self._current_player = color_map.get(next_player, self._current_player)
            
            elif action in {"game_over", "surrender"}:
                # winner 可能是 user_id；优先使用 winner_color
                winner_color = payload.get("winner_color")
                winner = payload.get("winner")
                if isinstance(winner_color, int):
                    self._winner = winner_color
                elif isinstance(winner, str) and self._room_state:
                    color_map = {
                        p.user_id: (1 if i == 0 else 2)
                        for i, p in enumerate(self._room_state.current_players)
                    }
                    self._winner = color_map.get(winner, 0)
                elif isinstance(winner, int):
                    self._winner = winner
                else:
                    self._winner = 0
                self._state = GameState.FINISHED
            
            elif action == "reset":
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
                
                # 本地检测胜负，保证无服务器时也能结束
                winner = self._check_winner(row, col)
                if winner:
                    self._winner = winner
                    self._state = GameState.FINISHED
                elif self._is_board_full():
                    self._winner = 0  # 平局
                    self._state = GameState.FINISHED
    
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
        
        # 如果没有网络回调（本地演示模式），直接应用
        if not self._context or not self._context.send_network:
            self._apply_move(row, col, self._current_player)
        
        return True
    
    def on_mouse_down(self, button: int, x: int, y: int) -> None:
        """处理鼠标点击"""
        if button == 1:  # 左键
            # 将屏幕坐标转换为棋盘坐标（由 UI 层实现）
            pass
    
    def undo_last_move(self) -> bool:
        """悔棋（仅本地或演示使用）"""
        # 线上对局：不支持悔棋（避免与服务器状态不一致）
        if self._context and self._context.send_network:
            return False

        if not self._history or self._state == GameState.FINISHED:
            return False
        
        last_row, last_col, player = self._history.pop()
        self._board[last_row][last_col] = 0
        self._last_move = self._history[-1][:2] if self._history else None
        self._current_player = player  # 还原到落子方
        self._winner = 0
        self._state = GameState.PLAYING
        return True
    
    def surrender(self) -> None:
        """认输（本地标记结果；服务器侧可扩展 action）"""
        if self._state != GameState.PLAYING:
            return

        # 线上对局：发送到服务器，由服务器权威结束
        if self._context and self._context.send_network:
            self.send_input({"action": "surrender"})
            # 本地乐观更新（服务器会很快广播 game_end）
            self._winner = 3 - self._my_color if self._my_color else 0
            self._state = GameState.FINISHED
            return

        # 演示模式：本地结束
        self._winner = 3 - self._my_color if self._my_color else 0
        self._state = GameState.FINISHED
    
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

    # ========== 本地工具 ==========
    def _check_winner(self, row: int, col: int) -> int:
        """本地判断是否五连"""
        player = self._board[row][col]
        if player == 0:
            return 0
        
        directions = [
            (0, 1),   # 水平
            (1, 0),   # 垂直
            (1, 1),   # 主对角
            (1, -1),  # 副对角
        ]
        
        for dr, dc in directions:
            count = 1
            # 正向
            r, c = row + dr, col + dc
            while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and self._board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # 反向
            r, c = row - dr, col - dc
            while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and self._board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 5:
                return player
        return 0

    def _is_board_full(self) -> bool:
        """是否棋盘已满"""
        return all(cell != 0 for row in self._board for cell in row)
