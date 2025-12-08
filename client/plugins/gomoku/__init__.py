"""
五子棋游戏插件
"""
from typing import TYPE_CHECKING

from .game import GomokuPlugin

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免在缺少 GUI 依赖（如 libGL）的环境中触发 ImportError
    from .widget import GomokuWidget

__all__ = ["GomokuPlugin", "GomokuWidget"]


def __getattr__(name: str):
    """按需加载 GUI 组件。

    运行环境可能缺少 Qt 依赖，延迟导入可避免在仅测试游戏逻辑时的加载失败。
    """

    if name == "GomokuWidget":
        from .widget import GomokuWidget  # 本地导入以延迟依赖解析

        return GomokuWidget
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
