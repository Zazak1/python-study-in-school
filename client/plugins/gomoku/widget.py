"""
五子棋游戏界面
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient, QFont
from typing import Optional, Tuple, List

from client.shell.styles.theme import CURRENT_THEME as t


class GomokuBoard(QWidget):
    """五子棋棋盘"""
    
    stone_placed = Signal(int, int)  # row, col
    
    BOARD_SIZE = 15
    CELL_SIZE = 36
    MARGIN = 30
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.board = [[0] * self.BOARD_SIZE for _ in range(self.BOARD_SIZE)]
        self.last_move: Optional[Tuple[int, int]] = None
        self.my_color = 1  # 1=黑, 2=白
        self.current_player = 1
        self.hover_pos: Optional[Tuple[int, int]] = None
        self.is_my_turn = False
        self.winner = 0
        
        # 计算尺寸
        size = self.MARGIN * 2 + self.CELL_SIZE * (self.BOARD_SIZE - 1)
        self.setFixedSize(size, size)
        self.setMouseTracking(True)
        
        # 样式
        self.setStyleSheet("background: transparent;")
    
    def set_board(self, board: List[List[int]]):
        """设置棋盘状态"""
        self.board = board
        self.update()
    
    def set_state(self, current_player: int, my_color: int, 
                  last_move: Optional[Tuple[int, int]], winner: int):
        """设置游戏状态"""
        self.current_player = current_player
        self.my_color = my_color
        self.last_move = last_move
        self.winner = winner
        self.is_my_turn = (current_player == my_color and winner == 0)
        self.update()
    
    def _board_to_pixel(self, row: int, col: int) -> Tuple[int, int]:
        """棋盘坐标转像素坐标"""
        x = self.MARGIN + col * self.CELL_SIZE
        y = self.MARGIN + row * self.CELL_SIZE
        return x, y
    
    def _pixel_to_board(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """像素坐标转棋盘坐标"""
        col = round((x - self.MARGIN) / self.CELL_SIZE)
        row = round((y - self.MARGIN) / self.CELL_SIZE)
        
        if 0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE:
            return row, col
        return None
    
    def paintEvent(self, event):
        """绘制棋盘"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制棋盘背景
        self._draw_board_background(painter)
        
        # 绘制网格线
        self._draw_grid(painter)
        
        # 绘制星位
        self._draw_star_points(painter)
        
        # 绘制悬停提示
        if self.hover_pos and self.is_my_turn:
            self._draw_hover(painter, *self.hover_pos)
        
        # 绘制棋子
        self._draw_stones(painter)
        
        # 绘制最后落子标记
        if self.last_move:
            self._draw_last_move_marker(painter, *self.last_move)
    
    def _draw_board_background(self, painter: QPainter):
        """绘制棋盘背景"""
        # 木纹色背景
        painter.setBrush(QBrush(QColor("#DEB887")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # 内边框
        pen = QPen(QColor("#8B7355"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        margin = 15
        inner_rect = self.rect().adjusted(margin, margin, -margin, -margin)
        painter.drawRect(inner_rect)
    
    def _draw_grid(self, painter: QPainter):
        """绘制网格"""
        pen = QPen(QColor("#4A3728"))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 水平线
        for i in range(self.BOARD_SIZE):
            x1, y1 = self._board_to_pixel(i, 0)
            x2, y2 = self._board_to_pixel(i, self.BOARD_SIZE - 1)
            painter.drawLine(x1, y1, x2, y2)
        
        # 垂直线
        for i in range(self.BOARD_SIZE):
            x1, y1 = self._board_to_pixel(0, i)
            x2, y2 = self._board_to_pixel(self.BOARD_SIZE - 1, i)
            painter.drawLine(x1, y1, x2, y2)
    
    def _draw_star_points(self, painter: QPainter):
        """绘制星位（天元和四个角星）"""
        painter.setBrush(QBrush(QColor("#4A3728")))
        painter.setPen(Qt.NoPen)
        
        star_positions = [
            (3, 3), (3, 11), (11, 3), (11, 11),  # 四角星
            (7, 7)  # 天元
        ]
        
        for row, col in star_positions:
            x, y = self._board_to_pixel(row, col)
            painter.drawEllipse(QPoint(x, y), 4, 4)
    
    def _draw_hover(self, painter: QPainter, row: int, col: int):
        """绘制悬停提示"""
        if self.board[row][col] != 0:
            return
        
        x, y = self._board_to_pixel(row, col)
        
        # 半透明棋子
        color = QColor("#222222" if self.my_color == 1 else "#FFFFFF")
        color.setAlpha(100)
        
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(x, y), 14, 14)
    
    def _draw_stones(self, painter: QPainter):
        """绘制棋子"""
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                stone = self.board[row][col]
                if stone != 0:
                    self._draw_stone(painter, row, col, stone)
    
    def _draw_stone(self, painter: QPainter, row: int, col: int, color: int):
        """绘制单个棋子"""
        x, y = self._board_to_pixel(row, col)
        radius = 15
        
        if color == 1:  # 黑子
            # 渐变效果
            gradient = QRadialGradient(x - 4, y - 4, radius * 1.5)
            gradient.setColorAt(0, QColor("#555555"))
            gradient.setColorAt(1, QColor("#111111"))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
        else:  # 白子
            gradient = QRadialGradient(x - 4, y - 4, radius * 1.5)
            gradient.setColorAt(0, QColor("#FFFFFF"))
            gradient.setColorAt(1, QColor("#DDDDDD"))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor("#AAAAAA"), 1))
        
        painter.drawEllipse(QPoint(x, y), radius, radius)
    
    def _draw_last_move_marker(self, painter: QPainter, row: int, col: int):
        """绘制最后落子标记"""
        x, y = self._board_to_pixel(row, col)
        
        # 红色小圆点
        painter.setBrush(QBrush(QColor("#EF4444")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(x, y), 4, 4)
    
    def mouseMoveEvent(self, event):
        """鼠标移动"""
        pos = self._pixel_to_board(event.position().x(), event.position().y())
        if pos != self.hover_pos:
            self.hover_pos = pos
            self.update()
    
    def mousePressEvent(self, event):
        """鼠标点击"""
        if event.button() != Qt.LeftButton:
            return
        
        if not self.is_my_turn:
            return
        
        pos = self._pixel_to_board(event.position().x(), event.position().y())
        if pos:
            row, col = pos
            if self.board[row][col] == 0:
                self.stone_placed.emit(row, col)
    
    def leaveEvent(self, event):
        """鼠标离开"""
        self.hover_pos = None
        self.update()


class PlayerInfo(QFrame):
    """玩家信息"""
    
    def __init__(self, is_left: bool = True, parent=None):
        super().__init__(parent)
        self.is_left = is_left
        self.is_current = False
        self.is_me = False
        
        self.setFixedSize(180, 80)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # 头部
        header = QHBoxLayout()
        header.setSpacing(12)
        
        # 棋子图标
        self.stone_label = QLabel()
        self.stone_label.setFixedSize(32, 32)
        self.stone_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.stone_label)
        
        # 名字
        self.name_label = QLabel("等待加入...")
        self.name_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {t.text_display};
        """)
        header.addWidget(self.name_label, 1)
        
        layout.addLayout(header)
        
        # 状态
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"""
            font-size: 12px;
            color: {t.text_caption};
        """)
        layout.addWidget(self.status_label)
        
        self._update_style()
    
    def set_player(self, name: str, color: int, is_me: bool = False):
        """设置玩家信息"""
        self.name_label.setText(name + (" (你)" if is_me else ""))
        self.is_me = is_me
        
        # 棋子图标
        stone_style = f"""
            background: {"#222222" if color == 1 else "#FFFFFF"};
            border: 2px solid {"#111111" if color == 1 else "#CCCCCC"};
            border-radius: 16px;
        """
        self.stone_label.setStyleSheet(stone_style)
        
        self._update_style()
    
    def set_current(self, is_current: bool):
        """设置是否是当前回合"""
        self.is_current = is_current
        self.status_label.setText("思考中..." if is_current else "等待对手")
        self._update_style()
    
    def _update_style(self):
        """更新样式"""
        if self.is_current:
            bg = f"{t.primary}15"
            border = t.primary
        else:
            bg = t.bg_card
            border = t.border_light
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 12px;
            }}
        """)


class GomokuWidget(QWidget):
    """五子棋游戏主界面"""
    
    game_exit = Signal()
    
    def __init__(self, plugin=None, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        
        # 模拟数据
        self.my_color = 1
        self.current_player = 1
        
        self.setup_ui()
        
        # 定时更新
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_from_plugin)
        self.update_timer.start(100)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
        # 标题栏
        header = QHBoxLayout()
        
        title = QLabel("⚫ 五子棋")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {t.text_display};
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # 退出按钮
        exit_btn = QPushButton("退出游戏")
        exit_btn.setCursor(Qt.PointingHandCursor)
        exit_btn.setFixedSize(100, 36)
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.error};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #DC2626;
            }}
        """)
        exit_btn.clicked.connect(self.game_exit.emit)
        header.addWidget(exit_btn)
        
        layout.addLayout(header)
        
        # 游戏区域
        game_area = QHBoxLayout()
        game_area.setSpacing(32)
        
        # 左侧玩家
        self.left_player = PlayerInfo(is_left=True)
        self.left_player.set_player("黑方", 1, True)
        game_area.addWidget(self.left_player, alignment=Qt.AlignTop)
        
        # 棋盘
        board_container = QVBoxLayout()
        
        self.board = GomokuBoard()
        self.board.stone_placed.connect(self._on_stone_placed)
        board_container.addWidget(self.board, alignment=Qt.AlignCenter)
        
        # 状态栏
        self.status_label = QLabel("黑方先行")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {t.text_display};
            padding: 12px;
        """)
        board_container.addWidget(self.status_label)
        
        game_area.addLayout(board_container, 1)
        
        # 右侧玩家
        self.right_player = PlayerInfo(is_left=False)
        self.right_player.set_player("白方", 2, False)
        game_area.addWidget(self.right_player, alignment=Qt.AlignTop)
        
        layout.addLayout(game_area, 1)
        
        # 底部操作栏
        footer = QHBoxLayout()
        
        # 悔棋
        self.undo_btn = QPushButton("悔棋")
        self.undo_btn.setCursor(Qt.PointingHandCursor)
        self.undo_btn.setFixedSize(80, 36)
        self.undo_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.bg_base};
                color: {t.text_body};
                border: 1px solid {t.border_normal};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {t.bg_hover};
            }}
        """)
        self.undo_btn.clicked.connect(self._on_undo)

        # 线上对局禁用悔棋（避免与服务器状态不一致）
        try:
            if self.plugin and self.plugin.context and self.plugin.context.send_network:
                self.undo_btn.setEnabled(False)
                self.undo_btn.setToolTip("线上对局不支持悔棋")
        except Exception:
            pass

        footer.addWidget(self.undo_btn)
        
        # 认输
        self.surrender_btn = QPushButton("认输")
        self.surrender_btn.setCursor(Qt.PointingHandCursor)
        self.surrender_btn.setFixedSize(80, 36)
        self.surrender_btn.setStyleSheet(f"""
            QPushButton {{
                background: {t.bg_base};
                color: {t.warning};
                border: 1px solid {t.warning};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {t.warning}15;
            }}
        """)
        self.surrender_btn.clicked.connect(self._on_surrender)
        footer.addWidget(self.surrender_btn)
        
        footer.addStretch()
        
        # 步数
        self.step_label = QLabel("第 0 步")
        self.step_label.setStyleSheet(f"color: {t.text_caption}; font-size: 13px;")
        footer.addWidget(self.step_label)
        
        layout.addLayout(footer)
        
        self._update_turn_display()
    
    def _on_stone_placed(self, row: int, col: int):
        """落子事件"""
        if self.plugin:
            success = self.plugin.place_stone(row, col)
            if success:
                # 本地预览（等服务器确认）
                pass
        else:
            # 演示模式：本地处理
            if self.board.board[row][col] == 0:
                self.board.board[row][col] = self.current_player
                self.board.last_move = (row, col)
                self.current_player = 3 - self.current_player
                self._update_turn_display()
                self.board.update()
    
    def _update_turn_display(self):
        """更新回合显示"""
        is_my_turn = (self.current_player == self.my_color)
        
        if self.current_player == 1:
            self.status_label.setText("黑方落子" if not is_my_turn else "轮到你了")
            self.left_player.set_current(True)
            self.right_player.set_current(False)
        else:
            self.status_label.setText("白方落子" if not is_my_turn else "轮到你了")
            self.left_player.set_current(False)
            self.right_player.set_current(True)
        
        self.board.set_state(
            self.current_player, 
            self.my_color, 
            self.board.last_move,
            0
        )
        
        # 更新步数
        step = sum(1 for row in self.board.board for cell in row if cell != 0)
        self.step_label.setText(f"第 {step} 步")
    
    def _update_from_plugin(self):
        """从插件更新状态"""
        if not self.plugin:
            return
        
        state = self.plugin.get_board_state()
        
        self.board.set_board(state['board'])
        self.current_player = state['current_player']
        self.my_color = state['my_color']
        
        winner = state['winner']
        if winner:
            if winner == self.my_color:
                self.status_label.setText("🎉 你赢了！")
            else:
                self.status_label.setText("😔 你输了")
            self.status_label.setStyleSheet(f"""
                font-size: 20px;
                font-weight: 700;
                color: {t.success if winner == self.my_color else t.error};
                padding: 12px;
            """)
        
        self.board.set_state(
            self.current_player,
            self.my_color,
            state['last_move'],
            winner
        )
        
        self._update_turn_display()

    # ========== 操作按钮 ==========
    def _on_undo(self):
        """悔棋按钮"""
        if self.plugin:
            if self.plugin.undo_last_move():
                self._update_from_plugin()
            return
        
        # 演示模式：本地移除最后一步
        for r in range(self.board.BOARD_SIZE - 1, -1, -1):
            for c in range(self.board.BOARD_SIZE - 1, -1, -1):
                if self.board.board[r][c] != 0:
                    self.board.board[r][c] = 0
                    self.board.last_move = None
                    self.current_player = 3 - self.current_player
                    self._update_turn_display()
                    self.board.update()
                    return
    
    def _on_surrender(self):
        """认输按钮"""
        if self.plugin:
            self.plugin.surrender()
            # 线上对局：等待服务器结算
            try:
                if self.plugin.context and self.plugin.context.send_network:
                    self.status_label.setText("已认输，等待结算...")
                    self.board.setEnabled(False)
                    if hasattr(self, "surrender_btn"):
                        self.surrender_btn.setEnabled(False)
                    return
            except Exception:
                pass

            self._update_from_plugin()
            return
        
        # 演示模式：直接判定另一方获胜
        self.board.set_state(
            self.current_player,
            self.my_color,
            self.board.last_move,
            winner=3 - self.my_color
        )
        self.status_label.setText("你选择了认输")
