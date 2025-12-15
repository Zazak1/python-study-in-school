#!/bin/bash
# Aether Party 构建脚本 (Shell 版本)

set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 清理之前的构建
echo "清理旧的构建文件..."
rm -rf build dist *.spec

# 主脚本路径（使用正确的路径格式）
MAIN_SCRIPT="client/launcher/main.py"

# 检查主脚本是否存在
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "错误: 找不到主脚本文件 $MAIN_SCRIPT"
    exit 1
fi

# 资源目录
ASSETS_DIR="client/assets"

echo "="
echo "开始构建 Aether Party 客户端..."
echo "="
echo "主脚本: $MAIN_SCRIPT"
echo "资源目录: $ASSETS_DIR"
echo "="

# 构建命令
pyinstaller \
    --name=aether-party \
    --onefile \
    --windowed \
    --clean \
    --noconfirm \
    --add-data="$ASSETS_DIR:client/assets" \
    --hidden-import=PySide6.QtCore \
    --hidden-import=PySide6.QtWidgets \
    --hidden-import=PySide6.QtGui \
    --hidden-import=arcade \
    --hidden-import=websockets \
    --hidden-import=pydantic \
    --hidden-import=client.plugins \
    --hidden-import=client.plugins.gomoku \
    --hidden-import=client.plugins.shooter2d \
    --hidden-import=client.plugins.werewolf \
    --hidden-import=client.plugins.monopoly \
    --hidden-import=client.plugins.racing \
    "$MAIN_SCRIPT"

echo ""
echo "✅ 构建完成！"
echo "输出目录: dist/"

