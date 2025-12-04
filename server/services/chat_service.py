"""
聊天服务
"""
from typing import Dict, List, Any
from datetime import datetime

from ..models.game_event import ChatMessage
from ..gateway.connection import ConnectionManager
from ..gateway.handler import ServiceRegistry


class ChatService:
    """聊天服务"""
    
    # 消息限制
    MAX_MESSAGE_LENGTH = 500
    RATE_LIMIT_MESSAGES = 10  # 每分钟最大消息数
    RATE_LIMIT_WINDOW = 60    # 时间窗口（秒）
    
    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager
        
        # 消息历史 {channel: [ChatMessage]}
        self._history: Dict[str, List[ChatMessage]] = {
            "lobby": []
        }
        
        # 速率限制 {user_id: [timestamp]}
        self._rate_limits: Dict[str, List[float]] = {}
    
    async def send_message(self, user_id: str, channel: str, content: str) -> tuple:
        """
        发送消息
        
        Returns:
            (success, error_message)
        """
        # 内容检查
        content = content.strip()
        if not content:
            return False, "消息内容不能为空"
        
        if len(content) > self.MAX_MESSAGE_LENGTH:
            return False, f"消息过长，最多 {self.MAX_MESSAGE_LENGTH} 字符"
        
        # 速率限制
        if not self._check_rate_limit(user_id):
            return False, "发送太频繁，请稍后再试"
        
        # 获取用户信息
        auth_service = ServiceRegistry.get("auth_service")
        if not auth_service:
            return False, "服务错误"
        
        user = auth_service.get_user(user_id)
        if not user:
            return False, "用户不存在"
        
        # 内容过滤（可扩展）
        content = self._filter_content(content)
        
        # 创建消息
        message = ChatMessage(
            channel=channel,
            sender_id=user_id,
            sender_name=user.nickname,
            content=content
        )
        
        # 保存历史
        self._add_to_history(channel, message)
        
        # 广播消息
        await self._broadcast_message(channel, message, user_id)
        
        return True, ""
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """检查速率限制"""
        now = datetime.now().timestamp()
        
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []
        
        # 清理过期记录
        self._rate_limits[user_id] = [
            t for t in self._rate_limits[user_id]
            if now - t < self.RATE_LIMIT_WINDOW
        ]
        
        # 检查是否超限
        if len(self._rate_limits[user_id]) >= self.RATE_LIMIT_MESSAGES:
            return False
        
        # 记录本次发送
        self._rate_limits[user_id].append(now)
        return True
    
    def _filter_content(self, content: str) -> str:
        """内容过滤（敏感词等）"""
        # 简单的敏感词过滤示例
        # 实际应使用更完善的过滤方案
        sensitive_words = ["fuck", "shit"]
        
        for word in sensitive_words:
            content = content.replace(word, "*" * len(word))
        
        return content
    
    def _add_to_history(self, channel: str, message: ChatMessage):
        """添加到历史"""
        if channel not in self._history:
            self._history[channel] = []
        
        self._history[channel].append(message)
        
        # 只保留最近 100 条
        if len(self._history[channel]) > 100:
            self._history[channel] = self._history[channel][-100:]
    
    async def _broadcast_message(self, channel: str, message: ChatMessage, sender_id: str):
        """广播消息"""
        msg_data = {
            "type": "chat_message",
            "channel": message.channel,
            "sender_id": message.sender_id,
            "sender_name": message.sender_name,
            "content": message.content,
            "timestamp": message.timestamp
        }
        
        if channel == "lobby":
            # 大厅消息：发送给所有订阅大厅的用户
            await self.conn_manager.send_to_channel("lobby", msg_data)
        
        elif channel.startswith("room_"):
            # 房间消息
            room_id = channel.replace("room_", "")
            await self.conn_manager.send_to_room(room_id, msg_data)
        
        elif channel.startswith("team_"):
            # 队伍消息
            await self.conn_manager.send_to_channel(channel, msg_data)
    
    def get_history(self, channel: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取历史消息"""
        messages = self._history.get(channel, [])
        return [
            {
                "sender_id": m.sender_id,
                "sender_name": m.sender_name,
                "content": m.content,
                "timestamp": m.timestamp
            }
            for m in messages[-limit:]
        ]

