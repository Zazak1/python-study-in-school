# Aether Party 🎮

**跨平台好友对战大厅** - 多游戏合集、实时社交、一键邀请好友开黑

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 特性

- 🖥️ **跨平台** - 支持 Windows 与 macOS
- 🎯 **多游戏合集** - 五子棋、2D 射击、狼人杀、大富翁、赛车竞速
- 💬 **实时社交** - 好友系统、房间聊天、语音通话
- 🔄 **帧同步** - 服务器权威 + 客户端预测，流畅体验
- 🔌 **插件化** - 游戏模块可独立开发与热更新

## 🏗️ 项目结构

```
python/
├── client/                 # 客户端代码
│   ├── launcher/          # 启动器（登录、更新）
│   ├── shell/             # 大厅 UI
│   ├── net/               # 网络模块
│   ├── plugins/           # 游戏插件
│   │   ├── base.py        # GamePlugin 基础接口
│   │   ├── gomoku/        # 五子棋
│   │   ├── shooter2d/     # 2D 射击
│   │   ├── werewolf/      # 狼人杀
│   │   ├── monopoly/      # 大富翁
│   │   └── racing/        # 赛车竞速
│   ├── assets/            # 游戏资源
│   └── services/          # 本地服务
├── docs/                   # 文档
│   └── TECHNICAL_SPEC.md  # 技术规格说明
├── tests/                  # 测试代码
├── requirements.txt        # 依赖列表
└── pyproject.toml          # 项目配置
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- pip 或 poetry

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/Zazak1/python-study-in-school.git
cd python-study-in-school

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖（可选）
pip install -e ".[dev]"
```

### 运行

```bash
# 启动服务器
python -m server.main

# 或使用 python3
python3 -m server.main

# 启动客户端
python -m client.launcher.main
```

**服务器配置说明：**
- 默认监听地址：`ws://0.0.0.0:8765`
- 可通过环境变量配置：
  - `SERVER_HOST`: 服务器地址（默认：0.0.0.0）
  - `SERVER_PORT`: 端口号（默认：8765）
  - `DEBUG`: 调试模式（默认：true）
  - `JWT_SECRET`: JWT密钥（生产环境请修改）
  - `DATABASE_URL`: 数据库URL（默认：sqlite:///aether_party.db）

## 🎮 游戏模块

| 游戏 | 状态 | 描述 |
|------|------|------|
| 五子棋 | 🟢 MVP 可玩 | 房间对战、落子校验、胜负判定 |
| 2D 射击 | 🟢 MVP 可玩 | 帧同步 + 键鼠操作（WASD+鼠标） |
| 狼人杀 | 🟢 MVP 可玩 | 阶段驱动、身份私发、查验/投票 |
| 大富翁 | 🟢 MVP 可玩 | 回合制：掷骰/买地/租金/破产 |
| 赛车竞速 | 🟢 MVP 可玩 | 倒计时 + 简化物理 + 圈数结算 |

## 🔧 技术栈

- **UI**: PySide6 (Qt for Python)
- **2D 渲染**: Arcade (基于 pyglet)
- **3D 渲染**: Panda3D (可选)
- **网络**: WebSocket + JSON/二进制
- **同步**: 服务器权威 + 客户端预测

## 📖 文档

- [技术规格说明](docs/TECHNICAL_SPEC.md) - 详细的架构与实现方案

## 🛣️ 路线图

- [x] 项目初始化与架构设计
- [x] GamePlugin 基础接口
- [x] 五子棋基础对战
- [x] 2D 射击帧同步
- [x] 大厅 UI 与房间/聊天
- [ ] 好友系统完善
- [ ] 语音聊天集成
- [ ] 更多游戏模块...

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)
