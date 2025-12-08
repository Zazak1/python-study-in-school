"""
主窗口
"""
import sys
import asyncio
import random
import time
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFontDatabase, QFont

from .styles import get_stylesheet, DARK_THEME
from .widgets import LoginWidget, LobbyWidget
from client.net import AuthManager, WebSocketManager, Message


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        # 网络/认证
        self.auth = AuthManager()
        self.ws_manager = None
        self._game_update_timer = QTimer()
        self._game_update_timer.setInterval(1000)
        self._game_update_timer.timeout.connect(self._on_mock_game_tick)
        self._frame_counter = 0
        self._current_game_id = None
        
        self.setup_window()
        self.setup_ui()
        self.connect_signals()
        self._init_network()
    
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
    
    # ========== 网络与认证 ==========
    def _init_network(self):
        """初始化 WebSocket 管理器并绑定回调"""
        # 连接回调
        def on_connect():
            self.lobby_widget.set_connection_status(True, "已连接服务器")
        
        def on_disconnect():
            self.lobby_widget.set_connection_status(False, "连接断开，尝试重连")
        
        def on_message(msg: Message):
            # 演示：将消息展示到游戏画面区域
            self.lobby_widget.set_game_render_data("服务器消息", {
                "type": msg.type,
                "payload": msg.payload,
                "msg_id": msg.msg_id,
                "timestamp": msg.timestamp
            })
        
        def on_binary(data: bytes):
            self.lobby_widget.set_game_render_data("二进制数据", {"length": len(data)})
        
        ws_url = "ws://0.0.0.0:8765/ws"
        self.ws_manager = WebSocketManager(
            url=ws_url,
            auth=self.auth,
            on_message=on_message,
            on_binary=on_binary,
            on_connect=on_connect,
            on_disconnect=on_disconnect,
        )
        
        async def mock_refresh(refresh_token: str):
            # 模拟刷新接口：立即返回新 token
            await asyncio.sleep(0)
            return {"token": f"{refresh_token}_refreshed", "expires_in": 3600}
        
        self.auth.set_refresh_handler(mock_refresh)
    
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
        
        # Mock 登录响应，后续可替换为真实接口
        login_resp = {
            "user_id": f"user_{username}",
            "username": username,
            "nickname": username,
            "avatar": "😎",
            "token": "dummy-token",
            "refresh_token": "dummy-refresh",
            "expires_in": 3600,
            "coins": 1680,
            "level": 1
        }
        self.auth.login(login_resp)
        
        # 更新大厅用户信息
        self.lobby_widget.profile_bar.set_user({
            'nickname': username,
            'avatar': '😎',
            'coins': 1680
        })
        
        # 建立 WebSocket 连接（使用最新 token）
        if self.ws_manager:
            self.ws_manager.connect()
        
        # 启动一个示例的本地渲染数据流（未真正连接服务器时的占位）
        self._start_mock_game_feed("gomoku", room_id="demo_room")
        
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
            
            # 断开 WS，清除会话
            if self.ws_manager:
                self.ws_manager.disconnect()
            self.auth.logout()
            self.lobby_widget.set_connection_status(False, "未连接")
            self._stop_mock_game_feed()
            
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
        # 更新游戏画面占位，等待实际房间/服务器数据接入
        if hasattr(self, "lobby_widget"):
            self.lobby_widget.set_game_render_data(
                f"预览：{game_name}",
                {"game": game_id, "status": "等待房间或服务器同步"}
            )
        
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
        
        if hasattr(self, "lobby_widget"):
            self.lobby_widget.set_game_render_data(
                "房间同步中",
                {"room_id": room_id, "status": "等待服务器状态"}
            )
        # 启动模拟的五子棋数据流
        self._start_mock_game_feed("gomoku", room_id=room_id)
        
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
        
        if hasattr(self, "lobby_widget"):
            self.lobby_widget.set_game_render_data(
                "匹配中",
                {"status": "正在匹配对手..."}
            )
        # 启动模拟的射击数据流
        self._start_mock_game_feed("shooter2d", room_id="match_demo")
        
        QMessageBox.information(
            self,
            "⚡ 快速匹配",
            "快速匹配功能开发中！\n\n"
            "完整版本将自动为你匹配合适的对手。"
        )
    
    # ========== 本地演示渲染流 ==========
    def _start_mock_game_feed(self, game_id: str, room_id: str):
        """启动本地模拟的游戏渲染数据流"""
        self._current_game_id = game_id
        self._frame_counter = 0
        self._game_update_timer.start()
    
    def _stop_mock_game_feed(self):
        self._game_update_timer.stop()
        self._current_game_id = None
        self._frame_counter = 0
    
    def _on_mock_game_tick(self):
        if not self._current_game_id:
            return
        
        self._frame_counter += 1
        now_ms = int(time.time() * 1000)
        
        if self._current_game_id == "gomoku":
            data = {
                "game": "gomoku",
                "frame": self._frame_counter,
                "board_size": 15,
                "last_move": [7, (7 + self._frame_counter) % 15],
                "current_player": "black" if self._frame_counter % 2 else "white",
                "status": "本地演示数据",
                "timestamp_ms": now_ms,
            }
        elif self._current_game_id == "shooter2d":
            data = {
                "game": "shooter2d",
                "frame": self._frame_counter,
                "players": [
                    {"user_id": "p1", "x": 100 + 5 * self._frame_counter, "y": 200, "hp": 90},
                    {"user_id": "p2", "x": 400, "y": 300, "hp": 100},
                ],
                "bullets": [
                    {"id": "b1", "x": 120 + 10 * self._frame_counter, "y": 210},
                ],
                "status": "本地演示数据",
                "timestamp_ms": now_ms,
            }
        else:
            data = {
                "game": self._current_game_id,
                "frame": self._frame_counter,
                "timestamp_ms": now_ms,
                "status": "本地演示数据",
            }
        
        self.lobby_widget.set_game_render_data(f"演示：{self._current_game_id}", data)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.ws_manager:
            try:
                self.ws_manager.shutdown()
            except Exception:
                pass
        self._stop_mock_game_feed()
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

