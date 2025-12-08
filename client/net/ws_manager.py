"""
WebSocket 管理器（后台事件循环）
将 WebSocketClient 放入独立 asyncio 线程，便于在 Qt 主线程中调用
"""
from __future__ import annotations

import asyncio
import threading
from typing import Callable, Dict, Any, Optional

from .websocket_client import WebSocketClient, Message
from .auth import AuthManager


class WebSocketManager:
    """在后台线程运行 WebSocketClient，提供线程安全的调用接口"""

    def __init__(
        self,
        url: str,
        auth: AuthManager,
        on_message: Optional[Callable[[Message], None]] = None,
        on_binary: Optional[Callable[[bytes], None]] = None,
        on_connect: Optional[Callable[[], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
    ):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        self._client = WebSocketClient(
            url=url,
            on_message=on_message,
            on_connect=on_connect,
            on_disconnect=on_disconnect,
            on_binary=on_binary,
        )
        self._client.set_token_provider(lambda: auth.token)

    def _run_coro(self, coro):
        """在线程安全地调度协程"""
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

    def connect(self) -> None:
        """发起连接（使用当前 token）"""
        self._run_coro(self._client.connect())

    def disconnect(self) -> None:
        """关闭连接"""
        self._run_coro(self._client.disconnect())

    def send(self, msg_type: str, payload: Dict[str, Any], requires_ack: bool = False):
        """发送文本消息"""
        return self._run_coro(self._client.send(msg_type, payload, requires_ack))

    def send_binary(self, data: bytes):
        """发送二进制消息"""
        return self._run_coro(self._client.send_binary(data))

    def shutdown(self):
        """停止事件循环与线程"""
        try:
            self.disconnect()
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread.is_alive():
            self._thread.join(timeout=2)

