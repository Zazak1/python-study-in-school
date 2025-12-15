#!/usr/bin/env python3
"""
Aether Party 构建脚本
使用 PyInstaller 打包客户端应用
"""
import os
import sys
import shutil
from pathlib import Path

def build_client():
    """构建客户端应用"""
    # 获取项目根目录
    root_dir = Path(__file__).parent
    os.chdir(root_dir)
    
    # 清理之前的构建
    build_dir = root_dir / "build"
    dist_dir = root_dir / "dist"
    spec_file = root_dir / "aether_party.spec"
    
    if build_dir.exists():
        print("清理旧的构建目录...")
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        print("清理旧的发布目录...")
        shutil.rmtree(dist_dir)
    if spec_file.exists():
        spec_file.unlink()
    
    # PyInstaller 命令参数
    main_script = root_dir / "client" / "launcher" / "main.py"
    
    if not main_script.exists():
        print(f"错误: 找不到主脚本文件 {main_script}")
        sys.exit(1)
    
    # 资源文件路径（使用绝对路径）
    assets_dir = root_dir / "client" / "assets"
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--name=aether-party",
        "--onefile",  # 单文件模式
        "--windowed",  # 无控制台窗口（macOS 使用 --noconsole）
        "--clean",
        "--noconfirm",
    ]
    
    # macOS 特定选项
    if sys.platform == "darwin":
        cmd.extend([
            "--osx-bundle-identifier=com.zazak1.aether-party",
            "--icon=NONE",  # 如果有图标文件可以指定
        ])
    
    # 添加资源文件
    if assets_dir.exists():
        # macOS 使用 : 分隔，Windows 使用 ;
        separator = ":" if sys.platform == "darwin" else ";"
        cmd.append(f"--add-data={assets_dir}{separator}client/assets")
    
    # 添加隐藏导入（PyInstaller 可能无法自动检测的模块）
    hidden_imports = [
        "PySide6.QtCore",
        "PySide6.QtWidgets",
        "PySide6.QtGui",
        "arcade",
        "websockets",
        "pydantic",
        "client.plugins",
        "client.plugins.gomoku",
        "client.plugins.shooter2d",
        "client.plugins.werewolf",
        "client.plugins.monopoly",
        "client.plugins.racing",
    ]
    
    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")
    
    # 添加主脚本
    cmd.append(str(main_script))
    
    print("=" * 60)
    print("开始构建 Aether Party 客户端...")
    print("=" * 60)
    print(f"主脚本: {main_script}")
    print(f"资源目录: {assets_dir}")
    print(f"构建命令: {' '.join(cmd)}")
    print("=" * 60)
    
    # 执行构建
    import subprocess
    result = subprocess.run(cmd, check=False)
    
    if result.returncode == 0:
        print("\n✅ 构建成功！")
        print(f"输出目录: {dist_dir}")
        if sys.platform == "darwin":
            app_path = dist_dir / "aether-party.app"
            if app_path.exists():
                print(f"应用包: {app_path}")
        else:
            exe_path = dist_dir / "aether-party.exe"
            if exe_path.exists():
                print(f"可执行文件: {exe_path}")
    else:
        print("\n❌ 构建失败！")
        sys.exit(1)


if __name__ == "__main__":
    build_client()

