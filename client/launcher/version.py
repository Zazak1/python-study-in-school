"""
版本管理 - 版本检查与资源校验
"""
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
import asyncio


@dataclass
class VersionInfo:
    """版本信息"""
    major: int
    minor: int
    patch: int
    build: int = 0
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other: 'VersionInfo') -> bool:
        return (self.major, self.minor, self.patch, self.build) < \
               (other.major, other.minor, other.patch, other.build)
    
    @classmethod
    def parse(cls, version_str: str) -> 'VersionInfo':
        """解析版本字符串"""
        parts = version_str.split('.')
        return cls(
            major=int(parts[0]) if len(parts) > 0 else 0,
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0
        )


@dataclass 
class AssetInfo:
    """资源信息"""
    path: str
    hash: str  # SHA256
    size: int
    version: str


class VersionManager:
    """版本管理器"""
    
    CURRENT_VERSION = VersionInfo(0, 1, 0)
    
    def __init__(self, app_dir: Path, assets_dir: Path):
        self.app_dir = app_dir
        self.assets_dir = assets_dir
        self.manifest_file = app_dir / "manifest.json"
        
        # 回调
        self.on_progress: Optional[Callable[[str, float], None]] = None
    
    def get_current_version(self) -> VersionInfo:
        """获取当前版本"""
        return self.CURRENT_VERSION
    
    def load_manifest(self) -> Dict[str, AssetInfo]:
        """加载资源清单"""
        if not self.manifest_file.exists():
            return {}
        
        try:
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                path: AssetInfo(**info) 
                for path, info in data.get('assets', {}).items()
            }
        except Exception as e:
            print(f"[VersionManager] 加载清单失败: {e}")
            return {}
    
    def save_manifest(self, assets: Dict[str, AssetInfo]):
        """保存资源清单"""
        data = {
            'version': str(self.CURRENT_VERSION),
            'assets': {
                path: {
                    'path': info.path,
                    'hash': info.hash,
                    'size': info.size,
                    'version': info.version
                }
                for path, info in assets.items()
            }
        }
        
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def compute_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def verify_assets(self) -> List[str]:
        """
        校验资源完整性
        
        Returns:
            损坏或缺失的资源列表
        """
        manifest = self.load_manifest()
        invalid_assets = []
        
        total = len(manifest)
        for i, (path, info) in enumerate(manifest.items()):
            if self.on_progress:
                self.on_progress(f"校验: {path}", (i + 1) / total)
            
            file_path = self.assets_dir / path
            
            # 检查文件是否存在
            if not file_path.exists():
                invalid_assets.append(path)
                continue
            
            # 检查哈希
            actual_hash = self.compute_file_hash(file_path)
            if actual_hash != info.hash:
                invalid_assets.append(path)
        
        return invalid_assets
    
    def scan_assets(self) -> Dict[str, AssetInfo]:
        """扫描资源目录，生成清单"""
        assets = {}
        
        if not self.assets_dir.exists():
            return assets
        
        files = list(self.assets_dir.rglob('*'))
        total = len(files)
        
        for i, file_path in enumerate(files):
            if file_path.is_file():
                if self.on_progress:
                    self.on_progress(f"扫描: {file_path.name}", (i + 1) / total)
                
                rel_path = file_path.relative_to(self.assets_dir)
                assets[str(rel_path)] = AssetInfo(
                    path=str(rel_path),
                    hash=self.compute_file_hash(file_path),
                    size=file_path.stat().st_size,
                    version=str(self.CURRENT_VERSION)
                )
        
        return assets
    
    async def check_for_updates(self, server_url: str) -> Optional[VersionInfo]:
        """
        检查更新
        
        Args:
            server_url: 更新服务器地址
            
        Returns:
            最新版本信息，如果有更新
        """
        # 模拟网络请求
        # 实际实现应使用 aiohttp
        await asyncio.sleep(0.5)
        
        # 模拟服务器返回
        server_version = VersionInfo(0, 1, 1)  # 假设服务器版本
        
        if self.CURRENT_VERSION < server_version:
            return server_version
        
        return None
    
    async def download_update(self, version: VersionInfo, server_url: str) -> bool:
        """
        下载更新
        
        Args:
            version: 目标版本
            server_url: 更新服务器地址
        """
        # 模拟下载
        for i in range(100):
            await asyncio.sleep(0.02)
            if self.on_progress:
                self.on_progress(f"下载更新 {version}", (i + 1) / 100)
        
        return True

