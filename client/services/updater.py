"""
更新检查器 - 版本管理与资源热更新
"""
import hashlib
import json
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Callable
from enum import Enum


class UpdateStatus(Enum):
    """更新状态"""
    CHECKING = "checking"
    UP_TO_DATE = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    ERROR = "error"


@dataclass
class VersionInfo:
    """版本信息"""
    version: str
    build_number: int
    release_date: str
    changelog: str
    download_url: str
    file_size: int
    checksum: str  # SHA256


@dataclass
class AssetPack:
    """资源包信息"""
    name: str
    version: str
    files: Dict[str, str]  # path -> hash
    download_url: str
    size: int


class UpdateChecker:
    """更新检查器"""
    
    def __init__(
        self,
        current_version: str,
        assets_dir: Path,
        update_url: str = "https://api.aether-party.com/updates"
    ):
        self.current_version = current_version
        self.assets_dir = assets_dir
        self.update_url = update_url
        
        self.status = UpdateStatus.UP_TO_DATE
        self.progress = 0.0
        self.latest_version: Optional[VersionInfo] = None
        
        # 回调
        self.on_status_change: Optional[Callable[[UpdateStatus], None]] = None
        self.on_progress: Optional[Callable[[float], None]] = None
    
    def _set_status(self, status: UpdateStatus):
        """设置状态"""
        self.status = status
        if self.on_status_change:
            self.on_status_change(status)
    
    def _set_progress(self, progress: float):
        """设置进度"""
        self.progress = progress
        if self.on_progress:
            self.on_progress(progress)
    
    async def check_for_updates(self) -> Optional[VersionInfo]:
        """检查更新"""
        self._set_status(UpdateStatus.CHECKING)
        
        try:
            # 模拟网络请求
            # 实际实现应使用 aiohttp
            await asyncio.sleep(1)
            
            # 模拟版本信息
            # 实际应从服务器获取
            server_version = "0.1.1"  # 假设服务器版本
            
            if self._compare_versions(server_version, self.current_version) > 0:
                self.latest_version = VersionInfo(
                    version=server_version,
                    build_number=102,
                    release_date="2024-01-15",
                    changelog="- 修复已知问题\n- 优化性能",
                    download_url=f"{self.update_url}/download/{server_version}",
                    file_size=50 * 1024 * 1024,  # 50MB
                    checksum="abc123..."
                )
                self._set_status(UpdateStatus.UPDATE_AVAILABLE)
                return self.latest_version
            else:
                self._set_status(UpdateStatus.UP_TO_DATE)
                return None
                
        except Exception as e:
            print(f"[UpdateChecker] 检查更新失败: {e}")
            self._set_status(UpdateStatus.ERROR)
            return None
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号"""
        def parse(v):
            return [int(x) for x in v.split('.')]
        
        p1, p2 = parse(v1), parse(v2)
        
        for a, b in zip(p1, p2):
            if a > b: return 1
            if a < b: return -1
        
        return len(p1) - len(p2)
    
    async def download_update(self) -> bool:
        """下载更新"""
        if not self.latest_version:
            return False
        
        self._set_status(UpdateStatus.DOWNLOADING)
        
        try:
            # 模拟下载
            total = 100
            for i in range(total):
                await asyncio.sleep(0.05)
                self._set_progress((i + 1) / total)
            
            self._set_status(UpdateStatus.INSTALLING)
            
            # 模拟安装
            await asyncio.sleep(2)
            
            self._set_status(UpdateStatus.UP_TO_DATE)
            return True
            
        except Exception as e:
            print(f"[UpdateChecker] 下载更新失败: {e}")
            self._set_status(UpdateStatus.ERROR)
            return False
    
    def verify_assets(self) -> Dict[str, bool]:
        """校验资源完整性"""
        results = {}
        
        if not self.assets_dir.exists():
            return results
        
        # 遍历资源文件
        for file_path in self.assets_dir.rglob('*'):
            if file_path.is_file():
                try:
                    # 计算文件哈希
                    sha256 = hashlib.sha256()
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(8192), b''):
                            sha256.update(chunk)
                    
                    # 这里应与服务器的哈希白名单比对
                    results[str(file_path.relative_to(self.assets_dir))] = True
                    
                except Exception:
                    results[str(file_path.relative_to(self.assets_dir))] = False
        
        return results
    
    async def check_assets(self) -> List[str]:
        """检查需要更新的资源"""
        # 实际应从服务器获取资源清单并比对
        missing = []
        
        # 检查必要资源是否存在
        required_assets = [
            "textures/ui/logo.png",
            "sounds/click.wav",
            "fonts/main.ttf"
        ]
        
        for asset in required_assets:
            asset_path = self.assets_dir / asset
            if not asset_path.exists():
                missing.append(asset)
        
        return missing

