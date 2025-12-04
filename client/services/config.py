"""
配置管理 - 应用配置与用户设置
"""
import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import base64
import hashlib


@dataclass
class UserSettings:
    """用户设置"""
    language: str = "zh-CN"
    theme: str = "light"
    sound_enabled: bool = True
    sound_volume: float = 0.8
    music_enabled: bool = True
    music_volume: float = 0.5
    notifications_enabled: bool = True
    auto_login: bool = False
    remember_password: bool = False


@dataclass
class NetworkSettings:
    """网络设置"""
    server_url: str = "ws://124.221.69.88:8765"
    timeout: int = 30
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    heartbeat_interval: int = 30


@dataclass
class GameSettings:
    """游戏设置"""
    fps_limit: int = 60
    vsync: bool = True
    show_fps: bool = False
    key_bindings: Dict[str, str] = field(default_factory=lambda: {
        "move_up": "W",
        "move_down": "S",
        "move_left": "A",
        "move_right": "D",
        "fire": "Space",
        "reload": "R"
    })


@dataclass
class AppConfig:
    """应用配置"""
    version: str = "0.1.0"
    user: UserSettings = field(default_factory=UserSettings)
    network: NetworkSettings = field(default_factory=NetworkSettings)
    game: GameSettings = field(default_factory=GameSettings)
    
    # 用户凭证（加密存储）
    saved_username: str = ""
    saved_token: str = ""  # 加密后的 token
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        config = cls()
        if 'user' in data:
            config.user = UserSettings(**data['user'])
        if 'network' in data:
            config.network = NetworkSettings(**data['network'])
        if 'game' in data:
            config.game = GameSettings(**data['game'])
        config.saved_username = data.get('saved_username', '')
        config.saved_token = data.get('saved_token', '')
        return config


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, app_name: str = "AetherParty"):
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self.config = AppConfig()
        
        # 加密密钥（基于机器特征生成）
        self._cipher = self._create_cipher()
        
        # 确保目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.load()
    
    def _get_config_dir(self) -> Path:
        """获取配置目录"""
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('APPDATA', '~'))
        else:  # macOS / Linux
            base = Path.home() / '.config'
        return base / self.app_name
    
    def _create_cipher(self) -> Fernet:
        """创建加密器（基于机器特征）"""
        # 使用机器名 + 用户名生成稳定密钥
        machine_id = f"{os.name}-{os.getlogin()}-{self.app_name}"
        key = hashlib.sha256(machine_id.encode()).digest()
        key_b64 = base64.urlsafe_b64encode(key)
        return Fernet(key_b64)
    
    def load(self) -> bool:
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = AppConfig.from_dict(data)
                return True
        except Exception as e:
            print(f"[ConfigManager] 加载配置失败: {e}")
        return False
    
    def save(self) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ConfigManager] 保存配置失败: {e}")
            return False
    
    def encrypt_token(self, token: str) -> str:
        """加密 token"""
        try:
            return self._cipher.encrypt(token.encode()).decode()
        except:
            return ""
    
    def decrypt_token(self, encrypted: str) -> str:
        """解密 token"""
        try:
            return self._cipher.decrypt(encrypted.encode()).decode()
        except:
            return ""
    
    def save_credentials(self, username: str, token: str):
        """保存用户凭证"""
        self.config.saved_username = username
        self.config.saved_token = self.encrypt_token(token)
        self.save()
    
    def get_saved_credentials(self) -> tuple:
        """获取保存的凭证"""
        username = self.config.saved_username
        token = self.decrypt_token(self.config.saved_token) if self.config.saved_token else ""
        return username, token
    
    def clear_credentials(self):
        """清除凭证"""
        self.config.saved_username = ""
        self.config.saved_token = ""
        self.save()

