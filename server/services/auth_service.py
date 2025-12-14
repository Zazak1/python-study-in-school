"""
认证服务
"""
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from ..config import config
from ..models.user import User, UserSession, UserStatus
from ..gateway.connection import Connection, ConnectionManager
from ..gateway.handler import ServiceRegistry


class AuthService:
    """认证服务"""
    
    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager
        
        # 模拟用户数据库（实际应使用数据库）
        self._users: Dict[str, User] = {}
        self._passwords: Dict[str, str] = {}  # username -> password_hash
        
        # 添加测试用户
        self._init_test_users()
    
    def _init_test_users(self):
        """初始化测试用户"""
        test_users = [
            ("test", "123456", "测试玩家", "😎"),
            ("alice", "123456", "Alice", "👩"),
            ("bob", "123456", "Bob", "👨"),
            ("charlie", "123456", "Charlie", "🧑"),
        ]
        
        for username, password, nickname, avatar in test_users:
            user_id = f"user_{username}"
            self._users[user_id] = User(
                user_id=user_id,
                username=username,
                nickname=nickname,
                avatar=avatar,
                coins=1000
            )
            self._passwords[username] = self._hash_password(password)
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self, user_id: str) -> str:
        """生成 JWT Token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=config.jwt_expire_hours),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)
    
    def _verify_token(self, token: str) -> Optional[str]:
        """验证 Token，返回 user_id"""
        try:
            payload = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
            return payload.get("user_id")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def login(self, connection: Connection, username: str, password: str, 
                   client_version: str = "", platform: str = "") -> Tuple[bool, Dict[str, Any]]:
        """
        登录
        
        Returns:
            (success, response_data)
        """
        # 验证密码
        password_hash = self._hash_password(password)
        if username not in self._passwords or self._passwords[username] != password_hash:
            return False, {"error": "用户名或密码错误"}
        
        # 获取用户
        user_id = f"user_{username}"
        user = self._users.get(user_id)
        if not user:
            return False, {"error": "用户不存在"}
        
        # 生成 Token
        token = self._generate_token(user_id)
        
        # 创建会话
        session = UserSession(
            user_id=user_id,
            connection_id=connection.connection_id,
            status=UserStatus.ONLINE,
            ip_address=str(connection.websocket.remote_address),
            client_version=client_version,
            platform=platform
        )
        
        # 认证连接
        await self.conn_manager.authenticate_connection(
            connection.connection_id, user_id, session
        )
        
        # 更新最后登录时间
        user.last_login = datetime.now()
        
        # 订阅大厅频道
        await self.conn_manager.subscribe_channel(connection.connection_id, "lobby")
        
        return True, {
            "user_id": user_id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "coins": user.coins,
            "level": user.level,
            "token": token,
            "expires_in": config.jwt_expire_hours * 3600
        }
    
    async def logout(self, connection: Connection):
        """登出"""
        if connection.user_id:
            # 取消订阅
            for channel in list(connection.channels):
                await self.conn_manager.unsubscribe_channel(connection.connection_id, channel)
            
            # 清除认证状态
            connection.is_authenticated = False
            connection.user_id = None
            connection.user_session = None
    
    async def token_login(self, connection: Connection, token: str) -> Tuple[bool, Dict[str, Any]]:
        """Token 登录（自动登录）"""
        user_id = self._verify_token(token)
        if not user_id:
            return False, {"error": "Token 无效或已过期"}
        
        user = self._users.get(user_id)
        if not user:
            return False, {"error": "用户不存在"}
        
        # 创建会话
        session = UserSession(
            user_id=user_id,
            connection_id=connection.connection_id,
            status=UserStatus.ONLINE
        )
        
        await self.conn_manager.authenticate_connection(
            connection.connection_id, user_id, session
        )
        
        await self.conn_manager.subscribe_channel(connection.connection_id, "lobby")
        
        return True, {
            "user_id": user_id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "coins": user.coins,
            "level": user.level,
            "token": token,
            "expires_in": config.jwt_expire_hours * 3600,
        }
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self._users.get(user_id)
    
    def register(self, username: str, password: str, nickname: str) -> Tuple[bool, str]:
        """注册新用户"""
        if username in self._passwords:
            return False, "用户名已存在"
        
        user_id = f"user_{username}"
        self._users[user_id] = User(
            user_id=user_id,
            username=username,
            nickname=nickname
        )
        self._passwords[username] = self._hash_password(password)
        
        return True, user_id
