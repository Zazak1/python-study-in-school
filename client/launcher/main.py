"""
Aether Party 启动器入口
"""
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_paths():
    """设置路径"""
    # 获取项目根目录
    root_dir = Path(__file__).parent.parent.parent
    
    # 资源目录
    assets_dir = root_dir / "client" / "assets"
    cache_dir = root_dir / ".cache"
    
    # 确保目录存在
    cache_dir.mkdir(exist_ok=True)
    
    return {
        "root": root_dir,
        "assets": assets_dir,
        "cache": cache_dir
    }


def main():
    """主入口"""
    logger.info("=" * 50)
    logger.info("Aether Party - 跨平台好友对战大厅")
    logger.info("=" * 50)
    
    # 设置路径
    paths = setup_paths()
    logger.info(f"项目根目录: {paths['root']}")
    logger.info(f"资源目录: {paths['assets']}")
    logger.info(f"缓存目录: {paths['cache']}")
    
    # 检查 PySide6
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        logger.info("PySide6 加载成功")
    except ImportError:
        logger.error("请先安装 PySide6: pip install PySide6")
        logger.info("运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 列出可用插件
    logger.info("可用的游戏插件:")
    from client.plugins.gomoku.game import GomokuPlugin
    from client.plugins.shooter2d.game import Shooter2DPlugin
    
    plugins = [GomokuPlugin, Shooter2DPlugin]
    for plugin_cls in plugins:
        plugin = plugin_cls()
        info = plugin.get_game_info()
        logger.info(f"  - {info['name']} v{info['version']}: {info['description']}")
        logger.info(f"    玩家数: {info['min_players']}-{info['max_players']}")
    
    logger.info("")
    logger.info("启动图形界面...")
    
    # 启动 UI
    from client.shell import run_app
    return run_app()


if __name__ == "__main__":
    sys.exit(main())

