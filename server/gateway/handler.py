"""
消息处理器
"""
import json
from typing import Dict, Any, Callable, Awaitable, Optional
from datetime import datetime

from .connection import Connection, ConnectionManager
from ..models.game_event import EventType


# 消息处理函数类型
HandlerFunc = Callable[[Connection, Dict[str, Any]], Awaitable[None]]


class MessageHandler:
    """消息路由与处理"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.conn_manager = connection_manager
        self._handlers: Dict[str, HandlerFunc] = {}
        
        # 注册内置处理器
        self._register_builtin_handlers()
    
    def register(self, event_type: str, handler: HandlerFunc):
        """注册消息处理器"""
        self._handlers[event_type] = handler
    
    def _register_builtin_handlers(self):
        """注册内置处理器"""
        self.register("heartbeat", self._handle_heartbeat)
    
    async def handle_message(self, connection: Connection, raw_message: str):
        """处理收到的消息"""
        try:
            # 解析 JSON
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await connection.send_error(4000, "无效的 JSON 格式")
                return
            
            # 获取消息类型
            event_type = message.get("type")
            if not event_type:
                await connection.send_error(4001, "缺少消息类型")
                return
            
            # 检查认证（部分消息需要认证）
            if not self._is_public_event(event_type) and not connection.is_authenticated:
                await connection.send_error(4003, "请先登录")
                return
            
            # 查找处理器
            handler = self._handlers.get(event_type)
            if not handler:
                await connection.send_error(4004, f"未知的消息类型: {event_type}")
                return
            
            # 执行处理器
            await handler(connection, message)
            
        except Exception as e:
            print(f"[MessageHandler] 处理消息异常: {e}")
            await connection.send_error(5000, "服务器内部错误")
    
    def _is_public_event(self, event_type: str) -> bool:
        """是否为公开事件（无需认证）"""
        return event_type in ["heartbeat", "login"]
    
    # ========== 内置处理器 ==========
    
    async def _handle_heartbeat(self, connection: Connection, message: Dict[str, Any]):
        """处理心跳"""
        connection.update_heartbeat()
        
        await connection.send({
            "type": "heartbeat_ack",
            "timestamp": datetime.now().timestamp()
        })


class ServiceRegistry:
    """服务注册表（用于依赖注入）"""
    
    _services: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, name: str, service: Any):
        """注册服务"""
        cls._services[name] = service
    
    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        """获取服务"""
        return cls._services.get(name)
    
    @classmethod
    def clear(cls):
        """清空"""
        cls._services.clear()

