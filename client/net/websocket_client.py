"""
WebSocket 客户端管理
负责连接、重连、心跳、可靠消息封装
"""
import asyncio
import json
import time
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
from enum import Enum, auto
import logging
import random

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """连接状态"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    CLOSED = auto()


@dataclass
class Message:
    """消息结构"""
    type: str
    payload: Dict[str, Any]
    msg_id: str = ""
    timestamp: float = 0.0
    requires_ack: bool = False


class WebSocketClient:
    """
    WebSocket 客户端
    
    功能：
    - 自动重连
    - 心跳检测
    - 消息序列化/反序列化
    - 可靠消息（需要确认的消息）
    """
    
    def __init__(
        self,
        url: str,
        on_message: Optional[Callable[[Message], None]] = None,
        on_connect: Optional[Callable[[], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
        on_binary: Optional[Callable[[bytes], None]] = None,
        heartbeat_interval: float = 30.0,
        reconnect_interval: float = 5.0,
        max_reconnect_attempts: int = 10
    ):
        self._url = url
        self._on_message = on_message
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_binary = on_binary
        
        self._heartbeat_interval = heartbeat_interval
        self._reconnect_interval = reconnect_interval
        self._max_reconnect_attempts = max_reconnect_attempts
        
        self._state = ConnectionState.DISCONNECTED
        self._websocket = None
        self._reconnect_attempts = 0
        
        # 消息队列与确认
        self._pending_messages: Dict[str, Message] = {}
        self._msg_counter = 0
        
        # 任务管理
        self._tasks: list = []
        self._running = False
        self._token_provider: Optional[Callable[[], str]] = None
    
    @property
    def state(self) -> ConnectionState:
        return self._state
    
    @property
    def is_connected(self) -> bool:
        return self._state == ConnectionState.CONNECTED
    
    def set_token_provider(self, provider: Callable[[], str]) -> None:
        """设置 token 提供器，用于重连时获取最新 token"""
        self._token_provider = provider
    
    async def connect(self, token: str = "") -> bool:
        """
        连接到服务器
        
        Args:
            token: JWT 认证 token
            
        Returns:
            是否连接成功
        """
        if self._state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
            return self._state == ConnectionState.CONNECTED
        
        self._state = ConnectionState.CONNECTING
        self._running = True
        
        try:
            # 动态导入 websockets
            import websockets
            
            # 构建连接 URL（带 token）
            token_to_use = token or (self._token_provider() if self._token_provider else "")
            url = f"{self._url}?token={token_to_use}" if token_to_use else self._url
            
            # 尝试连接，忽略代理设置（如果环境变量设置了代理但不需要）
            try:
                self._websocket = await websockets.connect(
                    url,
                    ping_interval=self._heartbeat_interval,
                    ping_timeout=10
                )
            except Exception as proxy_error:
                # 如果是因为代理问题，尝试不使用代理
                if "SOCKS" in str(proxy_error) or "proxy" in str(proxy_error).lower():
                    logger.warning(f"代理连接失败，尝试直连: {proxy_error}")
                    # 临时清除代理环境变量
                    import os
                    old_proxy = os.environ.pop("HTTP_PROXY", None)
                    old_https_proxy = os.environ.pop("HTTPS_PROXY", None)
                    old_all_proxy = os.environ.pop("ALL_PROXY", None)
                    try:
                        self._websocket = await websockets.connect(
                            url,
                            ping_interval=self._heartbeat_interval,
                            ping_timeout=10
                        )
                    finally:
                        # 恢复环境变量
                        if old_proxy:
                            os.environ["HTTP_PROXY"] = old_proxy
                        if old_https_proxy:
                            os.environ["HTTPS_PROXY"] = old_https_proxy
                        if old_all_proxy:
                            os.environ["ALL_PROXY"] = old_all_proxy
                else:
                    raise
            
            self._state = ConnectionState.CONNECTED
            self._reconnect_attempts = 0
            
            logger.info(f"Connected to {self._url}")
            
            if self._on_connect:
                self._on_connect()
            
            # 启动消息接收循环
            self._tasks.append(asyncio.create_task(self._receive_loop()))
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self._state = ConnectionState.DISCONNECTED
            return False
    
    async def disconnect(self) -> None:
        """断开连接"""
        self._running = False
        self._state = ConnectionState.CLOSED
        
        # 取消所有任务
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        
        logger.info("Disconnected")
        
        if self._on_disconnect:
            self._on_disconnect()
    
    async def send(self, msg_type: str, payload: Dict[str, Any], requires_ack: bool = False) -> str:
        """
        发送消息
        
        Args:
            msg_type: 消息类型
            payload: 消息内容
            requires_ack: 是否需要确认
            
        Returns:
            消息 ID
        """
        if not self.is_connected or not self._websocket:
            raise ConnectionError("Not connected")
        
        self._msg_counter += 1
        msg_id = f"{int(time.time() * 1000)}_{self._msg_counter}"
        
        message = Message(
            type=msg_type,
            payload=payload,
            msg_id=msg_id,
            timestamp=time.time(),
            requires_ack=requires_ack
        )
        
        data = json.dumps({
            "type": message.type,
            "payload": message.payload,
            "msg_id": message.msg_id,
            "timestamp": message.timestamp
        })
        
        await self._websocket.send(data)
        
        if requires_ack:
            self._pending_messages[msg_id] = message
        
        return msg_id
    
    async def send_binary(self, data: bytes) -> None:
        """发送二进制数据"""
        if not self.is_connected or not self._websocket:
            raise ConnectionError("Not connected")
        
        await self._websocket.send(data)
    
    async def _receive_loop(self) -> None:
        """消息接收循环"""
        try:
            import websockets
            
            while self._running and self._websocket:
                try:
                    data = await self._websocket.recv()
                    
                    if isinstance(data, str):
                        self._handle_text_message(data)
                    else:
                        self._handle_binary_message(data)
                        
                except websockets.ConnectionClosed:
                    logger.warning("Connection closed by server")
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Receive error: {e}")
        
        # 连接断开，尝试重连
        if self._running:
            self._state = ConnectionState.DISCONNECTED
            if self._on_disconnect:
                self._on_disconnect()
            asyncio.create_task(self._reconnect())
    
    def _handle_text_message(self, data: str) -> None:
        """处理文本消息"""
        try:
            msg_data = json.loads(data)
            
            # 处理 ACK 消息
            if msg_data.get("type") == "ack":
                ack_id = msg_data.get("msg_id")
                if ack_id in self._pending_messages:
                    del self._pending_messages[ack_id]
                return
            
            msg_type = msg_data.get("type", "unknown")
            reserved = {"type", "msg_id", "timestamp", "payload"}

            # 兼容两种格式：
            # 1) {type, payload:{...}}
            # 2) {type, ...业务字段...}
            payload = msg_data.get("payload")
            if isinstance(payload, dict):
                # 合并顶层业务字段（若服务端未用 payload 包裹）
                for k, v in msg_data.items():
                    if k in reserved:
                        continue
                    payload.setdefault(k, v)
            else:
                payload = {k: v for k, v in msg_data.items() if k not in reserved}

            message = Message(
                type=msg_type,
                payload=payload,
                msg_id=msg_data.get("msg_id", ""),
                timestamp=msg_data.get("timestamp", 0),
            )
            
            if self._on_message:
                self._on_message(message)
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {e}")
    
    def _handle_binary_message(self, data: bytes) -> None:
        """处理二进制消息"""
        # 二进制消息通常用于帧同步数据；交给上层处理
        if self._on_binary:
            try:
                self._on_binary(data)
            except Exception as e:
                logger.error(f"Binary handler error: {e}")
        else:
            logger.debug(f"Received binary message, len={len(data)}")
    
    async def _reconnect(self) -> None:
        """重连逻辑"""
        if self._state == ConnectionState.CLOSED:
            return
        
        self._state = ConnectionState.RECONNECTING
        
        while self._reconnect_attempts < self._max_reconnect_attempts and self._running:
            self._reconnect_attempts += 1
            logger.info(f"Reconnecting... attempt {self._reconnect_attempts}")
            
            # 指数退避 + 少量随机抖动，避免雪崩
            backoff = self._reconnect_interval * (2 ** (self._reconnect_attempts - 1))
            backoff = min(backoff, 60)
            jitter = random.uniform(0, 0.3 * backoff)
            await asyncio.sleep(backoff + jitter)
            
            if await self.connect():
                return
        
        logger.error("Max reconnect attempts reached")
        self._state = ConnectionState.DISCONNECTED


class ReliableChannel:
    """
    可靠消息通道
    
    提供消息重传和确认机制
    """
    
    def __init__(self, client: WebSocketClient, timeout: float = 5.0, max_retries: int = 3):
        self._client = client
        self._timeout = timeout
        self._max_retries = max_retries
        self._pending: Dict[str, asyncio.Future] = {}
    
    async def send_reliable(self, msg_type: str, payload: Dict[str, Any]) -> bool:
        """
        发送可靠消息（等待确认）
        
        Returns:
            是否发送成功（收到确认）
        """
        for attempt in range(self._max_retries):
            try:
                msg_id = await self._client.send(msg_type, payload, requires_ack=True)
                
                # 等待确认
                await asyncio.wait_for(
                    self._wait_for_ack(msg_id),
                    timeout=self._timeout
                )
                return True
                
            except asyncio.TimeoutError:
                logger.warning(f"Message {msg_type} timeout, attempt {attempt + 1}")
                continue
            except Exception as e:
                logger.error(f"Send error: {e}")
                break
        
        return False
    
    async def _wait_for_ack(self, msg_id: str) -> None:
        """等待消息确认"""
        while msg_id in self._client._pending_messages:
            await asyncio.sleep(0.1)
