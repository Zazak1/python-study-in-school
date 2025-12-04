"""
认证管理 - JWT 鉴权与 Token 管理
"""
import jwt
import time
import hashlib
import hmac
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class UserSession:
    """用户会话"""
    user_id: str
    username: str
    nickname: str
    avatar: str
    token: str
    refresh_token: str
    expires_at: float
    coins: int = 0
    level: int = 1
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'coins': self.coins,
            'level': self.level
        }


class AuthManager:
    """认证管理器"""
    
    def __init__(self, secret_key: str = ""):
        self.secret_key = secret_key or "aether-party-secret"
        self.session: Optional[UserSession] = None
    
    @property
    def is_logged_in(self) -> bool:
        """是否已登录"""
        return self.session is not None and not self.session.is_expired()
    
    @property
    def user(self) -> Optional[Dict[str, Any]]:
        """当前用户信息"""
        return self.session.to_dict() if self.session else None
    
    @property
    def token(self) -> str:
        """当前 Token"""
        return self.session.token if self.session else ""
    
    def login(self, response_data: Dict[str, Any]) -> bool:
        """
        处理登录响应，创建会话
        
        Args:
            response_data: 服务器返回的登录响应
        """
        try:
            self.session = UserSession(
                user_id=response_data.get('user_id', ''),
                username=response_data.get('username', ''),
                nickname=response_data.get('nickname', ''),
                avatar=response_data.get('avatar', ''),
                token=response_data.get('token', ''),
                refresh_token=response_data.get('refresh_token', ''),
                expires_at=time.time() + response_data.get('expires_in', 3600),
                coins=response_data.get('coins', 0),
                level=response_data.get('level', 1)
            )
            return True
        except Exception as e:
            print(f"[AuthManager] 登录处理失败: {e}")
            return False
    
    def logout(self):
        """登出"""
        self.session = None
    
    def get_auth_header(self) -> Dict[str, str]:
        """获取认证请求头"""
        if self.session:
            return {"Authorization": f"Bearer {self.session.token}"}
        return {}
    
    def sign_request(self, payload: Dict[str, Any]) -> str:
        """
        对请求签名（防篡改）
        
        Args:
            payload: 请求数据
            
        Returns:
            HMAC 签名
        """
        # 按 key 排序后拼接
        sorted_items = sorted(payload.items())
        data_str = "&".join(f"{k}={v}" for k, v in sorted_items)
        
        # HMAC-SHA256 签名
        signature = hmac.new(
            self.secret_key.encode(),
            data_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证 JWT Token（本地验证，仅用于检查格式）
        
        实际验证应在服务器端进行
        """
        try:
            # 解码但不验证签名（客户端没有服务器密钥）
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            # 检查过期时间
            if payload.get('exp', 0) < time.time():
                return None
            
            return payload
            
        except jwt.InvalidTokenError:
            return None
    
    async def refresh_token(self) -> bool:
        """
        刷新 Token
        
        实际实现需要调用服务器 API
        """
        if not self.session or not self.session.refresh_token:
            return False
        
        # TODO: 调用服务器刷新接口
        # response = await api.refresh_token(self.session.refresh_token)
        # if response.success:
        #     self.session.token = response.token
        #     self.session.expires_at = time.time() + response.expires_in
        #     return True
        
        return False
    
    def create_login_payload(self, username: str, password: str) -> Dict[str, Any]:
        """
        创建登录请求负载
        
        Args:
            username: 用户名
            password: 密码
        """
        # 密码哈希（不明文传输）
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        payload = {
            "username": username,
            "password_hash": password_hash,
            "timestamp": int(time.time()),
            "client_version": "0.1.0"
        }
        
        # 添加签名
        payload["signature"] = self.sign_request(payload)
        
        return payload

