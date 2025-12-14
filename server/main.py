"""
Aether Party 服务器入口
"""
import asyncio
import signal
import sys
from datetime import datetime

from .config import config
from .gateway import WebSocketServer, ConnectionManager, MessageHandler
from .gateway.handler import ServiceRegistry
from .services import AuthService, UserService, RoomService, MatchService, ChatService
from .games.game_service import GameService
from .models.room import RoomState
from .models.user import UserStatus


class AetherPartyServer:
    """Aether Party 游戏服务器"""
    
    def __init__(self):
        self.ws_server = WebSocketServer()
        self.conn_manager = self.ws_server.conn_manager
        self.message_handler = self.ws_server.message_handler
        
        # 初始化服务
        self._init_services()
        
        # 注册消息处理器
        self._register_handlers()
    
    def _init_services(self):
        """初始化所有服务"""
        # 认证服务
        self.auth_service = AuthService(self.conn_manager)
        ServiceRegistry.register("auth_service", self.auth_service)
        
        # 用户服务
        self.user_service = UserService(self.conn_manager)
        ServiceRegistry.register("user_service", self.user_service)
        
        # 房间服务
        self.room_service = RoomService(self.conn_manager)
        ServiceRegistry.register("room_service", self.room_service)
        
        # 匹配服务
        self.match_service = MatchService(self.conn_manager)
        ServiceRegistry.register("match_service", self.match_service)
        
        # 聊天服务
        self.chat_service = ChatService(self.conn_manager)
        ServiceRegistry.register("chat_service", self.chat_service)
        
        # 游戏服务
        self.game_service = GameService(self.conn_manager)
        ServiceRegistry.register("game_service", self.game_service)
    
    def _register_handlers(self):
        """注册消息处理器"""
        handler = self.message_handler
        
        # 认证
        handler.register("login", self._handle_login)
        handler.register("token_login", self._handle_token_login)
        handler.register("register", self._handle_register)
        handler.register("logout", self._handle_logout)
        
        # 大厅
        handler.register("get_friends", self._handle_get_friends)
        handler.register("get_rooms", self._handle_get_rooms)
        
        # 房间
        handler.register("create_room", self._handle_create_room)
        handler.register("join_room", self._handle_join_room)
        handler.register("leave_room", self._handle_leave_room)
        handler.register("set_ready", self._handle_set_ready)
        handler.register("start_game", self._handle_start_game)
        
        # 匹配
        handler.register("quick_match", self._handle_quick_match)
        handler.register("cancel_match", self._handle_cancel_match)
        
        # 游戏
        handler.register("game_action", self._handle_game_action)
        
        # 聊天
        handler.register("chat_message", self._handle_chat_message)
    
    # ========== 消息处理器 ==========
    
    async def _handle_login(self, connection, message):
        """处理登录"""
        username = message.get("username", "")
        password = message.get("password", "")
        client_version = message.get("client_version", "")
        platform = message.get("platform", "")
        
        success, data = await self.auth_service.login(
            connection, username, password, client_version, platform
        )
        
        await connection.send({
            "type": "login_response",
            "success": success,
            **data
        })
        
        if success:
            # 发送好友列表
            friends = await self.user_service.get_friends(data["user_id"])
            await connection.send({
                "type": "friend_list",
                "friends": friends
            })
            
            # 发送房间列表
            rooms = self.room_service.get_rooms_list()
            await connection.send({
                "type": "room_list",
                "rooms": rooms
            })
            await self._resume_room_if_needed(connection, data["user_id"])

    async def _handle_token_login(self, connection, message):
        """处理 Token 登录（自动登录）"""
        token = message.get("token", "")

        success, data = await self.auth_service.token_login(connection, token)

        await connection.send(
            {
                "type": "login_response",
                "success": success,
                **data,
            }
        )

        if success:
            friends = await self.user_service.get_friends(data["user_id"])
            await connection.send({"type": "friend_list", "friends": friends})

            rooms = self.room_service.get_rooms_list()
            await connection.send({"type": "room_list", "rooms": rooms})
            await self._resume_room_if_needed(connection, data["user_id"])

    async def _resume_room_if_needed(self, connection, user_id: str):
        """断线重连恢复：若用户仍在房间/对局中，恢复房间与游戏状态。"""
        try:
            room = self.room_service.find_room_by_user(user_id)
        except Exception:
            room = None

        if not room:
            return

        if room.state in (RoomState.CLOSED, RoomState.FINISHED):
            return

        # 重新加入房间连接组，确保能收到 room/chat/game 广播
        await self.conn_manager.join_room(connection.connection_id, room.room_id)

        status = UserStatus.IN_GAME if room.state == RoomState.PLAYING else UserStatus.IN_ROOM
        try:
            await self.user_service.update_user_status(user_id, status, room.room_id, room.game_type)
        except Exception:
            pass

        await connection.send(
            {
                "type": "room_resume",
                "room_state": room.state.value,
                "room": room.to_public_dict(),
                "players": [
                    {
                        "user_id": p.user_id,
                        "nickname": p.nickname,
                        "avatar": p.avatar,
                        "is_host": p.is_host,
                        "is_ready": p.is_ready,
                        "slot": p.slot,
                    }
                    for p in room.players
                ],
            }
        )

        if room.state != RoomState.PLAYING:
            return

        # 先发 game_start（让客户端创建插件），再发私有信息（狼人杀身份牌等）
        state = await self.game_service.get_state(room.room_id)
        if state is not None:
            await connection.send({"type": "game_start", "game_type": room.game_type, **state})

        private_init = self.game_service.get_private_init(room.room_id, user_id)
        if private_init:
            await connection.send(private_init)

    async def _handle_register(self, connection, message):
        """处理注册"""
        username = message.get("username", "")
        password = message.get("password", "")
        nickname = message.get("nickname") or username

        success, result = self.auth_service.register(username, password, nickname)

        if success:
            await connection.send(
                {
                    "type": "register_response",
                    "success": True,
                    "user_id": result,
                }
            )
        else:
            await connection.send(
                {
                    "type": "register_response",
                    "success": False,
                    "error": result,
                }
            )
    
    async def _handle_logout(self, connection, message):
        """处理登出"""
        await self.auth_service.logout(connection)
        await connection.send({"type": "logout_response", "success": True})
    
    async def _handle_get_friends(self, connection, message):
        """获取好友列表"""
        if not connection.user_id:
            return
        
        friends = await self.user_service.get_friends(connection.user_id)
        await connection.send({
            "type": "friend_list",
            "friends": friends
        })
    
    async def _handle_get_rooms(self, connection, message):
        """获取房间列表"""
        game_type = message.get("game_type")
        rooms = self.room_service.get_rooms_list(game_type)
        await connection.send({
            "type": "room_list",
            "rooms": rooms
        })
    
    async def _handle_create_room(self, connection, message):
        """创建房间"""
        if not connection.user_id:
            return
        
        room = await self.room_service.create_room(
            user_id=connection.user_id,
            game_type=message.get("game_type", "gomoku"),
            name=message.get("name", ""),
            max_players=message.get("max_players"),
            is_private=message.get("is_private", False),
            password=message.get("password", "")
        )
        
        if room:
            await connection.send({
                "type": "create_room_response",
                "success": True,
                "room": room.to_public_dict()
            })
        else:
            await connection.send({
                "type": "create_room_response",
                "success": False,
                "error": "创建房间失败"
            })
    
    async def _handle_join_room(self, connection, message):
        """加入房间"""
        if not connection.user_id:
            return
        
        success, result = await self.room_service.join_room(
            user_id=connection.user_id,
            room_id=message.get("room_id", ""),
            password=message.get("password", "")
        )
        
        if success:
            await connection.send({
                "type": "join_room_response",
                "success": True,
                "room": result.to_public_dict()
            })
        else:
            await connection.send({
                "type": "join_room_response",
                "success": False,
                "error": result
            })
    
    async def _handle_leave_room(self, connection, message):
        """离开房间"""
        if not connection.user_id:
            return
        
        room_id = message.get("room_id", "")
        if connection.user_session:
            room_id = room_id or connection.user_session.current_room
        
        if room_id:
            # 若在游戏中主动离开，按断线/弃权处理，避免对局卡死
            try:
                room = self.room_service.get_room(room_id)
            except Exception:
                room = None

            if room and room.state == RoomState.PLAYING:
                try:
                    await self.room_service.handle_disconnect(connection.user_id, room_id)
                except Exception:
                    pass

            await self.room_service.leave_room(connection.user_id, room_id)
        
        await connection.send({
            "type": "leave_room_response",
            "success": True
        })
    
    async def _handle_set_ready(self, connection, message):
        """设置准备状态"""
        if not connection.user_id or not connection.user_session:
            return
        
        room_id = connection.user_session.current_room
        if room_id:
            await self.room_service.set_ready(
                connection.user_id, 
                room_id,
                message.get("is_ready", True)
            )
    
    async def _handle_start_game(self, connection, message):
        """开始游戏"""
        if not connection.user_id or not connection.user_session:
            return
        
        room_id = connection.user_session.current_room
        if room_id:
            success, result = await self.room_service.start_game(
                connection.user_id, room_id
            )
            
            if not success:
                await connection.send({
                    "type": "start_game_response",
                    "success": False,
                    "error": result
                })
    
    async def _handle_quick_match(self, connection, message):
        """快速匹配"""
        if not connection.user_id:
            return
        
        game_type = message.get("game_type", "gomoku")
        success, msg = await self.match_service.request_match(
            connection.user_id, game_type
        )
        
        if not success:
            await connection.send({
                "type": "match_error",
                "error": msg
            })
    
    async def _handle_cancel_match(self, connection, message):
        """取消匹配"""
        if not connection.user_id:
            return
        
        await self.match_service.cancel_match(connection.user_id)
    
    async def _handle_game_action(self, connection, message):
        """处理游戏行动"""
        if not connection.user_id or not connection.user_session:
            return
        
        room_id = connection.user_session.current_room
        if not room_id:
            return
        
        action = message.get("action", "")
        data = message.get("data", {})
        
        success, result = await self.game_service.process_action(
            connection.user_id, room_id, action, data
        )

        # 无论成功与否都回响应（用于私有结果：如狼人杀预言家查验）
        response = {
            "type": "game_action_response",
            "success": success,
            "request_action": action,
        }
        if isinstance(result, dict):
            response.update(result)
        await connection.send(response)
    
    async def _handle_chat_message(self, connection, message):
        """处理聊天消息"""
        if not connection.user_id:
            return
        
        channel = message.get("channel", "lobby")
        content = message.get("content", "")
        
        success, error = await self.chat_service.send_message(
            connection.user_id, channel, content
        )
        
        if not success:
            await connection.send({
                "type": "chat_error",
                "error": error
            })
    
    # ========== 服务器控制 ==========
    
    async def start(self):
        """启动服务器"""
        print("=" * 60)
        print("  Aether Party 游戏服务器")
        print("=" * 60)
        print(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  监听地址: ws://{config.host}:{config.port}")
        print(f"  调试模式: {config.debug}")
        print("=" * 60)
        
        # 启动匹配服务
        await self.match_service.start()
        
        # 启动 WebSocket 服务器
        await self.ws_server.start()
    
    async def stop(self):
        """停止服务器"""
        print("\n正在关闭服务器...")
        
        # 停止匹配服务
        await self.match_service.stop()
        
        # 清理游戏
        self.game_service.cleanup()
        
        # 停止 WebSocket 服务器
        await self.ws_server.stop()


async def main():
    """主函数"""
    server = AetherPartyServer()
    
    # 信号处理
    loop = asyncio.get_event_loop()
    
    def handle_signal():
        asyncio.create_task(server.stop())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            # Windows 不支持 add_signal_handler
            pass
    
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()


def run():
    """入口函数"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已停止")


if __name__ == "__main__":
    run()
