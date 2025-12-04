"""
用户服务
"""
from typing import List, Dict, Any, Optional

from ..models.user import User, UserStatus
from ..gateway.connection import ConnectionManager
from ..gateway.handler import ServiceRegistry


class UserService:
    """用户服务"""
    
    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager
    
    def get_online_users(self) -> List[Dict[str, Any]]:
        """获取在线用户列表"""
        online_users = []
        
        for user_id, conn_id in self.conn_manager._user_connections.items():
            conn = self.conn_manager.get_connection(conn_id)
            if conn and conn.user_session:
                auth_service = ServiceRegistry.get("auth_service")
                if auth_service:
                    user = auth_service.get_user(user_id)
                    if user:
                        online_users.append({
                            "user_id": user_id,
                            "nickname": user.nickname,
                            "avatar": user.avatar,
                            "status": conn.user_session.status.value,
                            "current_game": conn.user_session.current_game
                        })
        
        return online_users
    
    async def get_friends(self, user_id: str) -> List[Dict[str, Any]]:
        """获取好友列表"""
        auth_service = ServiceRegistry.get("auth_service")
        if not auth_service:
            return []
        
        user = auth_service.get_user(user_id)
        if not user:
            return []
        
        friends = []
        for friend_id in user.friends:
            friend = auth_service.get_user(friend_id)
            if friend:
                # 检查是否在线
                friend_conn = self.conn_manager.get_connection_by_user(friend_id)
                is_online = friend_conn is not None
                
                friend_info = {
                    "user_id": friend_id,
                    "nickname": friend.nickname,
                    "avatar": friend.avatar,
                    "is_online": is_online,
                }
                
                if is_online and friend_conn.user_session:
                    friend_info["status"] = friend_conn.user_session.status.value
                    friend_info["current_game"] = friend_conn.user_session.current_game
                    friend_info["in_game"] = friend_conn.user_session.status == UserStatus.IN_GAME
                
                friends.append(friend_info)
        
        # 在线的排前面
        friends.sort(key=lambda x: (not x.get("is_online", False), x["nickname"]))
        
        return friends
    
    async def add_friend(self, user_id: str, friend_id: str) -> bool:
        """添加好友"""
        auth_service = ServiceRegistry.get("auth_service")
        if not auth_service:
            return False
        
        user = auth_service.get_user(user_id)
        friend = auth_service.get_user(friend_id)
        
        if not user or not friend:
            return False
        
        if friend_id in user.friends:
            return False  # 已经是好友
        
        if friend_id in user.blocked:
            return False  # 被屏蔽
        
        # 双向添加
        user.friends.append(friend_id)
        friend.friends.append(user_id)
        
        # 通知对方
        await self.conn_manager.send_to_user(friend_id, {
            "type": "friend_request_accepted",
            "user_id": user_id,
            "nickname": user.nickname
        })
        
        return True
    
    async def remove_friend(self, user_id: str, friend_id: str) -> bool:
        """删除好友"""
        auth_service = ServiceRegistry.get("auth_service")
        if not auth_service:
            return False
        
        user = auth_service.get_user(user_id)
        friend = auth_service.get_user(friend_id)
        
        if not user or not friend:
            return False
        
        if friend_id in user.friends:
            user.friends.remove(friend_id)
        if user_id in friend.friends:
            friend.friends.remove(user_id)
        
        return True
    
    async def update_user_status(self, user_id: str, status: UserStatus, current_room: str = None, current_game: str = None):
        """更新用户状态"""
        conn = self.conn_manager.get_connection_by_user(user_id)
        if conn and conn.user_session:
            conn.user_session.status = status
            conn.user_session.current_room = current_room
            conn.user_session.current_game = current_game
            
            # 通知好友状态变化
            await self._notify_friends_status_change(user_id)
    
    async def _notify_friends_status_change(self, user_id: str):
        """通知好友状态变化"""
        auth_service = ServiceRegistry.get("auth_service")
        if not auth_service:
            return
        
        user = auth_service.get_user(user_id)
        if not user:
            return
        
        conn = self.conn_manager.get_connection_by_user(user_id)
        status_info = {
            "type": "friend_status",
            "user_id": user_id,
            "nickname": user.nickname,
            "is_online": conn is not None
        }
        
        if conn and conn.user_session:
            status_info["status"] = conn.user_session.status.value
            status_info["current_game"] = conn.user_session.current_game
        
        for friend_id in user.friends:
            await self.conn_manager.send_to_user(friend_id, status_info)

