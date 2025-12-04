"""
WebSocket 服务器
"""
import asyncio
import signal
from typing import Optional, Set
import websockets
from websockets.server import WebSocketServerProtocol, serve

from ..config import config
from .connection import ConnectionManager
from .handler import MessageHandler, ServiceRegistry


class WebSocketServer:
    """WebSocket 服务器"""
    
    def __init__(self):
        self.conn_manager = ConnectionManager()
        self.message_handler = MessageHandler(self.conn_manager)
        
        self._server: Optional[websockets.WebSocketServer] = None
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # 注册到服务注册表
        ServiceRegistry.register("connection_manager", self.conn_manager)
        ServiceRegistry.register("message_handler", self.message_handler)
    
    async def start(self, host: str = None, port: int = None):
        """启动服务器"""
        host = host or config.host
        port = port or config.port
        
        self._running = True
        
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # 启动 WebSocket 服务器
        self._server = await serve(
            self._handle_connection,
            host,
            port,
            ping_interval=config.heartbeat_interval,
            ping_timeout=config.heartbeat_timeout,
        )
        
        print(f"[WebSocketServer] 服务器启动于 ws://{host}:{port}")
        print(f"[WebSocketServer] 最大连接数: {config.max_connections}")
        
        # 等待服务器关闭
        await self._server.wait_closed()
    
    async def stop(self):
        """停止服务器"""
        print("[WebSocketServer] 正在关闭服务器...")
        self._running = False
        
        # 取消清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 关闭所有连接
        for conn in list(self.conn_manager._connections.values()):
            try:
                await conn.websocket.close(1001, "服务器关闭")
            except:
                pass
        
        # 关闭服务器
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        print("[WebSocketServer] 服务器已关闭")
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol):
        """处理新连接"""
        # 检查连接数限制
        if self.conn_manager.connection_count >= config.max_connections:
            await websocket.close(1013, "服务器已满")
            return
        
        # 添加连接
        connection = await self.conn_manager.add_connection(websocket)
        
        try:
            # 发送欢迎消息
            await connection.send({
                "type": "welcome",
                "server_version": "0.1.0",
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # 消息循环
            async for message in websocket:
                await self.message_handler.handle_message(connection, message)
                
        except websockets.ConnectionClosed as e:
            print(f"[WebSocketServer] 连接关闭: {connection.connection_id}, code={e.code}")
        except Exception as e:
            print(f"[WebSocketServer] 连接异常: {connection.connection_id}, {e}")
        finally:
            # 清理连接
            await self._on_disconnect(connection)
    
    async def _on_disconnect(self, connection):
        """连接断开时的清理"""
        # 通知服务层处理离线逻辑
        if connection.is_authenticated and connection.user_id:
            # 如果用户在房间中，通知房间服务
            room_service = ServiceRegistry.get("room_service")
            if room_service and connection.user_session:
                current_room = connection.user_session.current_room
                if current_room:
                    await room_service.handle_disconnect(connection.user_id, current_room)
        
        # 移除连接
        await self.conn_manager.remove_connection(connection.connection_id)
    
    async def _cleanup_loop(self):
        """定期清理死连接"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                cleaned = await self.conn_manager.cleanup_dead_connections(config.heartbeat_timeout)
                if cleaned > 0:
                    print(f"[WebSocketServer] 清理了 {cleaned} 个超时连接")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[WebSocketServer] 清理任务异常: {e}")


async def run_server():
    """运行服务器"""
    server = WebSocketServer()
    
    # 信号处理
    loop = asyncio.get_event_loop()
    
    def handle_signal():
        asyncio.create_task(server.stop())
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)
    
    await server.start()


if __name__ == "__main__":
    asyncio.run(run_server())

