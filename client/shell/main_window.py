"""
主窗口
"""
import os
import sys
import asyncio
import platform
from pathlib import Path
from typing import Any, Optional
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QDialog,
)
from PySide6.QtCore import Qt, QTimer, Signal

from .styles import get_stylesheet, DARK_THEME
from .widgets import ArenaWidget, LoginWidget, CreateRoomDialog, RegisterDialog
from client.net import AuthManager, WebSocketManager, Message
from client.services.game_session import GameSession


class MainWindow(QMainWindow):
    """主窗口"""

    # 网络线程 -> UI 线程信号（避免跨线程直接操作 Qt 控件）
    network_connected = Signal()
    network_disconnected = Signal()
    network_message = Signal(object)
    network_binary = Signal(bytes)
    
    def __init__(self):
        super().__init__()
        # 网络/认证
        self.auth = AuthManager()
        self.ws_manager = None
        self._pending_login: Optional[tuple[str, str, bool]] = None
        self._pending_register: Optional[dict[str, Any]] = None

        # 房间状态（用于 room/chat/game 路由）
        self._current_room_id: Optional[str] = None
        self._current_room: Optional[dict[str, Any]] = None
        self._current_room_players: list[dict[str, Any]] = []

        self.game_session: Optional[GameSession] = None
        
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
        
        # Arena 页面（大厅/房间/好友/设置）
        self.arena_widget = ArenaWidget()
        self.stack.addWidget(self.arena_widget)
        
        # 默认显示登录页面
        self.stack.setCurrentWidget(self.login_widget)
    
    def connect_signals(self):
        """连接信号"""
        # 登录信号
        self.login_widget.login_requested.connect(self.on_login)
        self.login_widget.register_requested.connect(self.on_register)

        # Arena 信号
        self.arena_widget.logout_requested.connect(self.on_logout)
        self.arena_widget.room_joined.connect(self._on_room_joined)
        self.arena_widget.create_room_requested.connect(self._on_room_created)
        self.arena_widget.quick_match_requested.connect(self._on_quick_match)

        self.arena_widget.leave_room_requested.connect(self._on_leave_room)
        self.arena_widget.start_game_requested.connect(self._on_start_game)

        # 聊天发送
        self.arena_widget.right_panel.chat_widget.message_sent.connect(self._on_chat_message_sent)

        # 网络事件（从网络线程发来）
        self.network_connected.connect(self._on_ws_connected)
        self.network_disconnected.connect(self._on_ws_disconnected)
        self.network_message.connect(self._on_ws_message)
        self.network_binary.connect(self._on_ws_binary)
    
    # ========== 网络与认证 ==========
    def _init_network(self):
        """初始化 WebSocket 管理器并绑定回调"""
        # 连接回调
        def on_connect():
            self.network_connected.emit()
        
        def on_disconnect():
            self.network_disconnected.emit()
        
        def on_message(msg: Message):
            self.network_message.emit(msg)
        
        def on_binary(data: bytes):
            self.network_binary.emit(data)
        
        # 允许通过环境变量覆盖服务器地址，便于打包后分发给好友使用
        # 例：AETHER_SERVER_URL=ws://124.221.69.88:8765/ws
        ws_url = os.getenv("AETHER_SERVER_URL", "ws://124.221.69.88:8765/ws")
        self.ws_manager = WebSocketManager(
            url=ws_url,
            auth=self.auth,
            on_message=on_message,
            on_binary=on_binary,
            on_connect=on_connect,
            on_disconnect=on_disconnect,
        )

        # 游戏会话（插件桥接）
        root_dir = Path(__file__).resolve().parents[2]
        assets_dir = root_dir / "client" / "assets"
        cache_dir = root_dir / ".cache"
        cache_dir.mkdir(exist_ok=True)
        self.game_session = GameSession(self.auth, self.ws_manager, assets_dir=assets_dir, cache_dir=cache_dir)
        
        async def mock_refresh(refresh_token: str):
            # 模拟刷新接口：立即返回新 token
            await asyncio.sleep(0)
            return {"token": f"{refresh_token}_refreshed", "expires_in": 3600}
        
        self.auth.set_refresh_handler(mock_refresh)
    
    def _on_ws_connected(self):
        self.arena_widget.set_connection_status(True, "已连接服务器")

        # 连接建立后：优先 token_login（用于断线重连），否则发送 pending login
        if self.auth.session and self.auth.token:
            self._send_token_login(self.auth.token)
        elif self._pending_register:
            payload = self._pending_register
            self._pending_register = None
            self._send_register(
                username=str(payload.get("username") or ""),
                password=str(payload.get("password") or ""),
                nickname=str(payload.get("nickname") or payload.get("username") or ""),
            )
        elif self._pending_login:
            username, password, _remember = self._pending_login
            self._send_login(username, password)

    def _on_ws_disconnected(self):
        self.arena_widget.set_connection_status(False, "连接断开，尝试重连")

    def _on_ws_binary(self, data: bytes):
        self.arena_widget.right_panel.chat_widget.add_message(
            {
                "sender_id": "server",
                "sender_name": "Server",
                "sender_color": "#64748B",
                "content": f"(binary) len={len(data)}",
            }
        )

    def _send_login(self, username: str, password: str):
        if not self.ws_manager:
            print("[MainWindow] 警告: ws_manager 未初始化")
            return
        print(f"[MainWindow] 发送登录请求: username={username}")
        self.ws_manager.send(
            "login",
            {
                "username": username,
                "password": password,
                "client_version": "0.1.0",
                "platform": platform.system().lower(),
            },
            requires_ack=True,
        )

    def _send_token_login(self, token: str):
        if not self.ws_manager:
            return
        self.ws_manager.send("token_login", {"token": token}, requires_ack=True)

    def _send_register(self, username: str, password: str, nickname: str):
        if not self.ws_manager:
            print("[MainWindow] 警告: ws_manager 未初始化")
            return
        if not username or not password:
            print("[MainWindow] 警告: 用户名或密码为空")
            return
        print(f"[MainWindow] 发送注册请求: username={username}, nickname={nickname}")
        self.ws_manager.send("register", {"username": username, "password": password, "nickname": nickname}, requires_ack=True)

    # ========== 登录相关 ==========

    def on_login(self, username: str, password: str, remember: bool):
        """处理登录请求"""
        self.login_widget.set_loading(True)
        self._pending_login = (username, password, remember)

        # 发起 WebSocket 连接；连接成功后在 _on_ws_connected 里发送 login/token_login
        if self.ws_manager:
            self.ws_manager.connect()
    
    def on_register(self):
        """处理注册请求"""
        dialog = RegisterDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        data = dialog.get_register_data()
        if not self.ws_manager:
            QMessageBox.warning(self, "注册失败", "网络未初始化")
            return

        # 已连接则直接发送；否则先连接，待 _on_ws_connected 再发送
        if getattr(self.ws_manager, "is_connected", False):
            self._send_register(
                username=str(data.get("username") or ""),
                password=str(data.get("password") or ""),
                nickname=str(data.get("nickname") or data.get("username") or ""),
            )
        else:
            self._pending_register = data
            self.ws_manager.connect()
    
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
            if self.game_session:
                self.game_session.stop()
            if self.ws_manager:
                self.ws_manager.disconnect()
            self.auth.logout()
            self.arena_widget.set_connection_status(False, "未连接")
            
            # 切换到登录页面
            self.stack.setCurrentWidget(self.login_widget)
            print("[退出登录]")

    def _on_room_joined(self, room_id: str):
        if not self.ws_manager:
            return
        self.ws_manager.send("join_room", {"room_id": room_id}, requires_ack=True)

    def _on_room_created(self):
        dialog = CreateRoomDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        if not self.ws_manager:
            return
        cfg = dialog.get_room_config()
        self.ws_manager.send("create_room", cfg, requires_ack=True)

    def _on_quick_match(self):
        if not self.ws_manager:
            return
        # MVP：默认 shooter2d
        self.ws_manager.send("quick_match", {"game_type": "shooter2d"}, requires_ack=True)

    def _on_leave_room(self):
        if not self.ws_manager:
            return
        room_id = self._current_room_id
        # 主动离开房间：停止当前插件，避免继续发输入/占用资源
        if self.game_session:
            self.game_session.stop()
        self.ws_manager.send("leave_room", {"room_id": room_id or ""}, requires_ack=True)

    def _on_start_game(self):
        if not self.ws_manager:
            return
        self.ws_manager.send("start_game", {}, requires_ack=True)

    def _on_chat_message_sent(self, channel: str, text: str):
        if not self.ws_manager:
            return
        # 映射 UI channel -> 服务端 channel
        send_channel = channel
        if channel == "room" and self._current_room_id:
            send_channel = f"room_{self._current_room_id}"
        elif channel == "team" and self._current_room_id:
            # 服务端目前仅支持 team_ 前缀广播；MVP 先复用房间频道
            send_channel = f"room_{self._current_room_id}"

        self.ws_manager.send(
            "chat_message",
            {"channel": send_channel, "content": text},
            requires_ack=False,
        )

    def _on_ws_message(self, msg: Message):
        msg_type = msg.type
        payload = msg.payload or {}

        if msg_type == "login_response":
            self._handle_login_response(payload)
            return

        if msg_type == "register_response":
            print(f"[MainWindow] 收到注册响应: success={payload.get('success')}, payload={payload}")
            if payload.get("success"):
                QMessageBox.information(self, "注册成功", "注册成功，请返回登录。")
            else:
                error_msg = str(payload.get("error") or "注册失败")
                print(f"[MainWindow] 注册失败: {error_msg}")
                QMessageBox.warning(self, "注册失败", error_msg)
            return

        if msg_type == "friend_list":
            friends = payload.get("friends", [])
            if isinstance(friends, list):
                self.arena_widget.right_panel.friends_widget.set_friends(friends)
            return

        if msg_type == "room_list":
            rooms = payload.get("rooms", [])
            if isinstance(rooms, list):
                self.arena_widget.lobby_view.rooms_widget.set_rooms(rooms)
            return

        if msg_type == "create_room_response":
            if payload.get("success"):
                room = payload.get("room") or {}
                self._enter_room_from_server(room)
            else:
                QMessageBox.warning(self, "创建房间失败", str(payload.get("error") or "创建房间失败"))
            return

        if msg_type == "join_room_response":
            if payload.get("success"):
                room = payload.get("room") or {}
                self._enter_room_from_server(room)
                # MVP：自动准备，方便房主直接开始游戏
                if self.ws_manager:
                    self.ws_manager.send("set_ready", {"is_ready": True}, requires_ack=True)
            else:
                QMessageBox.warning(self, "加入房间失败", str(payload.get("error") or "加入房间失败"))
            return

        if msg_type == "leave_room_response":
            if self.game_session:
                self.game_session.stop()
            self._current_room_id = None
            self._current_room = None
            self._current_room_players = []
            self.arena_widget.set_active_tab("lobby")
            return

        if msg_type == "room_resume":
            room = payload.get("room") or {}
            players = payload.get("players", [])
            if isinstance(players, list):
                self._current_room_players = players
            self._enter_room_from_server(room)
            return

        if msg_type == "match_found":
            room_id = payload.get("room_id")
            game_type = payload.get("game_type")
            self._current_room_id = str(room_id) if room_id else None
            self.arena_widget.set_active_tab("room")
            if room_id:
                from .widgets.arena_room_view import RoomDisplay

                title = f"{game_type or 'game'} 匹配房"
                self.arena_widget.room_view.set_room(RoomDisplay(room_id=str(room_id), title=title))
                self.arena_widget.room_view.begin_matchmaking()
            return

        if msg_type == "room_update":
            self._handle_room_update(payload)
            return

        if msg_type == "game_private":
            if self.game_session:
                self.game_session.handle_game_private(payload)
            return

        if msg_type == "game_action_response":
            if not payload.get("success"):
                self.arena_widget.right_panel.chat_widget.add_message(
                    {
                        "sender_id": "system",
                        "sender_name": "System",
                        "sender_color": "#64748B",
                        "content": f"[ActionError] {payload.get('error') or payload}",
                    }
                )
                return
            if self.game_session:
                self.game_session.handle_game_action_response(payload)
            return

        if msg_type == "game_start":
            self._handle_game_start(payload)
            return

        if msg_type == "game_action":
            if self.game_session:
                self.game_session.handle_game_action(payload)
            return

        if msg_type == "game_sync":
            if self.game_session:
                self.game_session.handle_game_sync(payload)
            return

        if msg_type in {"game_end", "game_over"}:
            self._handle_game_end(payload)
            return

        if msg_type == "chat_message":
            self._handle_chat_message(payload)
            return

        if msg_type in {"error", "chat_error", "match_error"}:
            self.arena_widget.right_panel.chat_widget.add_message(
                {
                    "sender_id": "system",
                    "sender_name": "System",
                    "sender_color": "#64748B",
                    "content": f"{msg_type}: {payload}",
                }
            )
            return

        # 默认：打印到聊天，便于调试
        self.arena_widget.right_panel.chat_widget.add_message(
            {
                "sender_id": "server",
                "sender_name": "Server",
                "sender_color": "#64748B",
                "content": f"{msg_type}: {payload}",
            }
        )

    def _handle_login_response(self, payload: dict[str, Any]):
        self.login_widget.set_loading(False)
        
        print(f"[MainWindow] 收到登录响应: success={payload.get('success')}, payload={payload}")

        if not payload.get("success"):
            error_msg = str(payload.get("error") or "用户名或密码错误")
            print(f"[MainWindow] 登录失败: {error_msg}")
            QMessageBox.warning(self, "登录失败", error_msg)
            return

        # 写入会话
        login_success = self.auth.login(payload)
        if not login_success:
            print("[MainWindow] 警告: AuthManager.login() 返回 False")
            QMessageBox.warning(self, "登录失败", "处理登录响应时出错")
            return

        # 设置“自己”的 ID，用于聊天气泡判断
        if self.auth.session:
            self.arena_widget.right_panel.chat_widget.set_local_user(self.auth.session.user_id)

        nickname = payload.get("nickname") or payload.get("username") or "Player"
        avatar = payload.get("avatar") or "👤"
        level = int(payload.get("level") or 1)
        self.arena_widget.set_user(nickname=nickname, avatar=avatar, level=level)

        # 进入大厅
        print("[MainWindow] 登录成功，切换到大厅")
        self.stack.setCurrentWidget(self.arena_widget)

    def _enter_room_from_server(self, room: dict[str, Any]):
        room_id = room.get("room_id")
        if room_id:
            self._current_room_id = str(room_id)
        self._current_room = room
        if self.game_session and self._current_room_id:
            self.game_session.set_room_snapshot(self._current_room_id, room, self._current_room_players)
        self.arena_widget.set_active_tab("room")

        from .widgets.arena_room_view import RoomDisplay

        title = room.get("name") or room.get("game_type") or "Room"
        self.arena_widget.room_view.set_room(RoomDisplay(room_id=str(self._current_room_id or ""), title=title))
        self.arena_widget.room_view.set_matching(False)

    def _handle_room_update(self, payload: dict[str, Any]):
        room = payload.get("room") or {}
        room_id = payload.get("room_id") or room.get("room_id")
        if room_id:
            self._current_room_id = str(room_id)
        self._current_room = room
        players = payload.get("players", [])
        if isinstance(players, list):
            self._current_room_players = players
        if self.game_session and self._current_room_id:
            self.game_session.set_room_snapshot(self._current_room_id, room, self._current_room_players)

        # 轻量提示
        action = payload.get("action")
        if action:
            self.arena_widget.right_panel.chat_widget.add_message(
                {
                    "sender_id": "system",
                    "sender_name": "System",
                    "sender_color": "#64748B",
                    "content": f"[房间] {action}: {room.get('name','')}",
                }
            )

    def _handle_chat_message(self, payload: dict[str, Any]):
        channel = payload.get("channel") or "lobby"

        # 只展示当前相关频道（大厅/当前房间）
        if channel.startswith("room_"):
            room_id = channel.replace("room_", "")
            if self._current_room_id and room_id != self._current_room_id:
                return

        # 发送端本地已回显，避免重复渲染
        if self.auth.session and payload.get("sender_id") == self.auth.session.user_id:
            return

        self.arena_widget.right_panel.chat_widget.add_message(
            {
                "sender_id": payload.get("sender_id", ""),
                "sender_name": payload.get("sender_name", "Unknown"),
                "sender_color": "#2563EB",
                "content": payload.get("content", ""),
            }
        )

    def _handle_game_start(self, payload: dict[str, Any]):
        if not self.game_session:
            return

        game_type = str(payload.get("game_type") or "")
        if not game_type:
            return

        try:
            plugin = self.game_session.start(game_type, payload)
        except Exception as e:
            self.arena_widget.right_panel.chat_widget.add_message(
                {
                    "sender_id": "system",
                    "sender_name": "System",
                    "sender_color": "#64748B",
                    "content": f"[GameStart] 初始化失败: {e}",
                }
            )
            return

        # 展示游戏 UI（MVP：尽量用专用 UI；兜底使用通用 JSON 展示）
        title = game_type
        if self._current_room and isinstance(self._current_room, dict):
            title = str(self._current_room.get("name") or self._current_room.get("game_type") or game_type)

        if game_type == "gomoku":
            from client.plugins.gomoku.widget import GomokuWidget

            widget = GomokuWidget(plugin=plugin)
            widget.game_exit.connect(self.arena_widget.room_view.show_match_ui)
        elif game_type == "shooter2d":
            from client.plugins.shooter2d.widget import Shooter2DWidget

            widget = Shooter2DWidget(plugin=plugin)
        elif game_type == "monopoly":
            from client.plugins.monopoly.widget import MonopolyWidget

            widget = MonopolyWidget(plugin=plugin)
        elif game_type == "werewolf":
            from client.plugins.werewolf.widget import WerewolfWidget

            widget = WerewolfWidget(plugin=plugin)
        elif game_type == "racing":
            from client.plugins.racing.widget import RacingWidget

            widget = RacingWidget(plugin=plugin)
        else:
            from .widgets.plugin_host_widget import PluginHostWidget

            widget = PluginHostWidget(plugin=plugin, game_type=game_type, title=title)

        self.arena_widget.room_view.show_game(title=title, widget=widget)

    def _handle_game_end(self, payload: dict[str, Any]):
        if self.game_session:
            self.game_session.handle_game_end(payload)
            self.game_session.stop()

        winner = payload.get("winner") or payload.get("winner_id")
        if winner:
            self.arena_widget.right_panel.chat_widget.add_message(
                {
                    "sender_id": "system",
                    "sender_name": "System",
                    "sender_color": "#64748B",
                    "content": f"[GameEnd] winner={winner}",
                }
            )
        self.arena_widget.room_view.show_match_ui()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.ws_manager:
            try:
                self.ws_manager.shutdown()
            except Exception:
                pass
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
