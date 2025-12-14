"""
大厅 UI 模块 - 好友/房间/聊天、通知中心
"""
from __future__ import annotations

from typing import Any

__all__ = ['MainWindow', 'run_app']


def __getattr__(name: str) -> Any:
    """
    延迟导入，避免在仅使用样式/插件时触发 UI 初始化导致的循环依赖。
    """
    if name in {"MainWindow", "run_app"}:
        from .main_window import MainWindow, run_app  # 局部导入

        return {"MainWindow": MainWindow, "run_app": run_app}[name]
    raise AttributeError(name)
