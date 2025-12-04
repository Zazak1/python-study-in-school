"""
主窗口
"""
import sys
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFontDatabase, QFont

from .styles import get_stylesheet, DARK_THEME
from .widgets import LoginWidget, LobbyWidget


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.setup_ui()
        self.connect_signals()
    
    def setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle("⚡ Aether Party - 跨平台好友对战大厅")
        self.setMinimumSize(1280, 800)
        self.resize(1400, 900)
        
        # 应用样式表
        self.setStyleSheet(get_stylesheet(DARK_THEME))
        
        # 设置窗口背景
        self.setAutoFillBackground(True)
    
    def setup_ui(self):
        """设置 UI"""
        # 中央堆栈窗口
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # 登录页面
        self.login_widget = LoginWidget()
        self.stack.addWidget(self.login_widget)
        
        # 大厅页面
        self.lobby_widget = LobbyWidget()
        self.stack.addWidget(self.lobby_widget)
        
        # 默认显示登录页面
        self.stack.setCurrentWidget(self.login_widget)
    
    def connect_signals(self):
        """连接信号"""
        # 登录信号
        self.login_widget.login_requested.connect(self.on_login)
        self.login_widget.register_requested.connect(self.on_register)
        
        # 大厅信号
        self.lobby_widget.game_selected.connect(self.on_game_selected)
        self.lobby_widget.room_joined.connect(self.on_room_joined)
        self.lobby_widget.room_created.connect(self.on_room_created)
        self.lobby_widget.quick_match_requested.connect(self.on_quick_match)
        self.lobby_widget.logout_requested.connect(self.on_logout)
    
    # ========== 登录相关 ==========
    
    def on_login(self, username: str, password: str, remember: bool):
        """处理登录请求"""
        print(f"[登录] 用户: {username}, 记住: {remember}")
        
        # 显示加载状态
        self.login_widget.set_loading(True)
        
        # 模拟登录延迟
        QTimer.singleShot(1000, lambda: self._complete_login(username))
    
    def _complete_login(self, username: str):
        """完成登录"""
        self.login_widget.set_loading(False)
        
        # 更新大厅用户信息
        self.lobby_widget.profile_bar.set_user({
            'nickname': username,
            'avatar': '😎',
            'coins': 1680
        })
        
        # 切换到大厅
        self.stack.setCurrentWidget(self.lobby_widget)
        
        print(f"[登录成功] 欢迎 {username}!")
    
    def on_register(self):
        """处理注册请求"""
        QMessageBox.information(
            self, 
            "注册", 
            "注册功能开发中...\n\n请使用任意用户名密码登录体验！"
        )
    
    def on_logout(self):
        """处理退出登录"""
        reply = QMessageBox.question(
            self,
            "退出登录",
            "确定要退出登录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 清空输入
            self.login_widget.username_input.clear()
            self.login_widget.password_input.clear()
            
            # 切换到登录页面
            self.stack.setCurrentWidget(self.login_widget)
            print("[退出登录]")
    
    # ========== 游戏相关 ==========
    
    def on_game_selected(self, game_id: str):
        """处理游戏选择"""
        game_names = {
            'gomoku': '五子棋',
            'shooter2d': '2D 射击',
            'werewolf': '狼人杀',
            'monopoly': '大富翁',
            'racing': '赛车竞速'
        }
        game_name = game_names.get(game_id, game_id)
        
        print(f"[选择游戏] {game_name}")
        
        QMessageBox.information(
            self,
            f"🎮 {game_name}",
            f"你选择了 {game_name}！\n\n"
            f"游戏功能开发中...\n"
            f"可以先创建房间或加入现有房间。"
        )
    
    def on_room_joined(self, room_id: str):
        """处理加入房间"""
        print(f"[加入房间] ID: {room_id}")
        
        QMessageBox.information(
            self,
            "加入房间",
            f"正在加入房间 #{room_id}...\n\n房间功能开发中！"
        )
    
    def on_room_created(self):
        """处理创建房间"""
        print("[创建房间]")
        
        QMessageBox.information(
            self,
            "创建房间",
            "创建房间功能开发中！\n\n"
            "完整版本将支持:\n"
            "• 选择游戏类型\n"
            "• 设置房间人数\n"
            "• 设置游戏规则\n"
            "• 邀请好友"
        )
    
    def on_quick_match(self):
        """处理快速匹配"""
        print("[快速匹配]")
        
        QMessageBox.information(
            self,
            "⚡ 快速匹配",
            "快速匹配功能开发中！\n\n"
            "完整版本将自动为你匹配合适的对手。"
        )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        reply = QMessageBox.question(
            self,
            "退出游戏",
            "确定要退出 Aether Party 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def run_app():
    """运行应用"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("Aether Party")
    app.setApplicationVersion("0.1.0")
    
    # 设置应用级样式
    app.setStyle("Fusion")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行事件循环
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_app())

