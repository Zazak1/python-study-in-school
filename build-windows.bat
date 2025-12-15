@echo off
REM Aether Party Windows 构建脚本
REM 在 Windows 系统上运行此脚本来构建 exe 文件

setlocal enabledelayedexpansion

echo ========================================
echo Aether Party Windows 构建脚本
echo ========================================
echo.

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 清理旧的构建文件
echo 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

REM 检查主脚本是否存在
set "MAIN_SCRIPT=client\launcher\main.py"
if not exist "%MAIN_SCRIPT%" (
    echo 错误: 找不到主脚本文件 %MAIN_SCRIPT%
    exit /b 1
)

REM 资源目录
set "ASSETS_DIR=client\assets"

echo.
echo ========================================
echo 开始构建...
echo ========================================
echo 主脚本: %MAIN_SCRIPT%
echo 资源目录: %ASSETS_DIR%
echo ========================================
echo.

REM 构建命令
pyinstaller ^
    --name=aether-party ^
    --onefile ^
    --windowed ^
    --noconsole ^
    --clean ^
    --noconfirm ^
    --add-data="%ASSETS_DIR%;client\assets" ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=arcade ^
    --hidden-import=websockets ^
    --hidden-import=pydantic ^
    --hidden-import=client.plugins ^
    --hidden-import=client.plugins.gomoku ^
    --hidden-import=client.plugins.shooter2d ^
    --hidden-import=client.plugins.werewolf ^
    --hidden-import=client.plugins.monopoly ^
    --hidden-import=client.plugins.racing ^
    "%MAIN_SCRIPT%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo 构建成功！
    echo ========================================
    echo 可执行文件位置: dist\aether-party.exe
    echo.
) else (
    echo.
    echo ========================================
    echo 构建失败！
    echo ========================================
    exit /b 1
)

pause

