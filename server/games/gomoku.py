"""
五子棋游戏逻辑（服务器权威）
"""
from typing import Dict, Any, List, Optional, Tuple
from .base import GameLogic, GameResult
from ..models.room import Room


class GomokuGame(GameLogic):
    """五子棋游戏"""
    
    GAME_TYPE = "gomoku"
    BOARD_SIZE = 15
    WIN_COUNT = 5
    
    def __init__(self, room: Room):
        super().__init__(room)
        self.board: List[List[int]] = []
        self.history: List[Tuple[int, int, int]] = []  # (row, col, player)
        self.player_colors: Dict[str, int] = {}  # user_id -> 1(黑) or 2(白)
    
    def init_game(self) -> Dict[str, Any]:
        """初始化游戏"""
        # 初始化棋盘
        self.board = [[0] * self.BOARD_SIZE for _ in range(self.BOARD_SIZE)]
        self.history = []
        self.winner = None
        self.is_finished = False
        
        # 分配颜色（先加入的玩家为黑方）
        players = self.room.players
        if len(players) >= 2:
            self.player_colors[players[0].user_id] = 1  # 黑
            self.player_colors[players[1].user_id] = 2  # 白
            self.current_player = players[0].user_id
        
        # 初始状态
        self.state = {
            "board": self.board,
            "current_player": self.current_player,
            "player_colors": self.player_colors,
        }
        
        return {
            "type": "game_start",
            "game_type": self.GAME_TYPE,
            "board_size": self.BOARD_SIZE,
            "player_colors": self.player_colors,
            "current_player": self.current_player,
            "your_color": None  # 由客户端根据自己的 user_id 判断
        }
    
    def process_action(self, user_id: str, action: str, data: Dict[str, Any]) -> tuple:
        """处理落子"""
        if action == "surrender":
            if self.is_finished:
                return False, {"error": "游戏已结束"}, None
            if user_id not in self.player_colors:
                return False, {"error": "无效玩家"}, None

            winner_id: Optional[str] = None
            for uid in self.player_colors:
                if uid != user_id:
                    winner_id = uid
                    break

            self.winner = winner_id
            self.is_finished = True

            return True, {"success": True}, {
                "type": "game_action",
                "action": "surrender",
                "loser": user_id,
                "winner": winner_id,
                "winner_color": self.player_colors.get(winner_id) if winner_id else None,
                "game_over": True,
                "reason": "surrender",
                "frame_id": len(self.history),
            }

        if action != "move":
            return False, {"error": "未知操作"}, None
        
        # 验证是否轮到该玩家
        if user_id != self.current_player:
            return False, {"error": "还没轮到你"}, None
        
        row = data.get("row")
        col = data.get("col")
        
        # 验证坐标
        if not self._is_valid_position(row, col):
            return False, {"error": "无效的位置"}, None
        
        # 验证位置是否为空
        if self.board[row][col] != 0:
            return False, {"error": "该位置已有棋子"}, None
        
        # 落子
        player_color = self.player_colors[user_id]
        self.board[row][col] = player_color
        self.history.append((row, col, player_color))
        
        # 检查胜负
        winner_color = self._check_winner(row, col)
        
        # 切换玩家
        self._switch_player()
        
        # 构建广播数据
        broadcast = {
            "type": "game_action",
            "action": "move",
            "row": row,
            "col": col,
            "player": player_color,
            "player_id": user_id,
            "next_player": self.current_player,
            "frame_id": len(self.history)
        }
        
        # 检查游戏结束
        if winner_color:
            self.winner = user_id
            self.is_finished = True
            broadcast["game_over"] = True
            broadcast["winner"] = user_id
            broadcast["winner_color"] = winner_color
        elif self._is_board_full():
            self.is_finished = True
            broadcast["game_over"] = True
            broadcast["winner"] = None  # 平局
        
        return True, {"success": True}, broadcast
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "board": self.board,
            "current_player": self.current_player,
            "player_colors": self.player_colors,
            "history": self.history,
            "winner": self.winner,
            "is_finished": self.is_finished,
            "frame_id": len(self.history)
        }
    
    def check_game_over(self) -> Optional[GameResult]:
        """检查游戏结束"""
        if not self.is_finished:
            return None
        
        scores = {}
        for user_id, color in self.player_colors.items():
            if user_id == self.winner:
                scores[user_id] = 100  # 胜者得分
            elif self.winner is None:
                scores[user_id] = 50   # 平局得分
            else:
                scores[user_id] = 0    # 负者得分
        
        return GameResult(
            winner_id=self.winner,
            scores=scores,
            stats={
                "total_moves": len(self.history),
                "board_state": self.board
            }
        )
    
    def handle_disconnect(self, user_id: str) -> Dict[str, Any]:
        """处理断线（对方获胜）"""
        if user_id in self.player_colors and not self.is_finished:
            # 断线判负
            for uid in self.player_colors:
                if uid != user_id:
                    self.winner = uid
                    break
            self.is_finished = True
            
            return {
                "type": "game_over",
                "reason": "disconnect",
                "winner": self.winner,
                "disconnected": user_id
            }
        
        return {"disconnected": user_id}
    
    # ========== 私有方法 ==========
    
    def _is_valid_position(self, row: int, col: int) -> bool:
        """验证位置是否有效"""
        return (isinstance(row, int) and isinstance(col, int) and
                0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE)
    
    def _switch_player(self):
        """切换当前玩家"""
        for user_id, color in self.player_colors.items():
            if user_id != self.current_player:
                self.current_player = user_id
                break
    
    def _check_winner(self, row: int, col: int) -> Optional[int]:
        """
        检查是否获胜
        
        Returns:
            获胜的颜色 (1 或 2)，或 None
        """
        player = self.board[row][col]
        if player == 0:
            return None
        
        # 四个方向：水平、垂直、两条对角线
        directions = [
            (0, 1),   # 水平
            (1, 0),   # 垂直
            (1, 1),   # 主对角线
            (1, -1),  # 副对角线
        ]
        
        for dr, dc in directions:
            count = 1
            
            # 正方向
            r, c = row + dr, col + dc
            while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE:
                if self.board[r][c] == player:
                    count += 1
                    r += dr
                    c += dc
                else:
                    break
            
            # 反方向
            r, c = row - dr, col - dc
            while 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE:
                if self.board[r][c] == player:
                    count += 1
                    r -= dr
                    c -= dc
                else:
                    break
            
            if count >= self.WIN_COUNT:
                return player
        
        return None
    
    def _is_board_full(self) -> bool:
        """检查棋盘是否已满"""
        for row in self.board:
            if 0 in row:
                return False
        return True
