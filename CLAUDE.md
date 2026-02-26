# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ClawMultiDeploy** - 用于在 Windows 系统下通过 Docker 部署多个完全隔离的 OpenClaw 实例，提供可视化 Web 界面实现便捷的多实例管理与运维。

## Technology Stack

### 后端
- **框架**: FastAPI (Python)
- **数据库**: SQLite
- **包管理**: uv
- **任务执行**: PowerShell 脚本集成

### 前端
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI 组件**: Element Plus
- **状态管理**: Pinia

### 基础设施
- **容器化**: Docker, Docker Compose
- **目标应用**: [OpenClaw](https://github.com/openclaw/openclaw.git)

## Architecture

### 目录结构

```
openclaw-deploy/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── models.py                 # SQLite 数据模型
│   │   ├── database.py               # 数据库连接
│   │   ├── schemas.py                # Pydantic 模型
│   │   ├── routers/                  # API 路由
│   │   │   ├── instances.py          # 实例管理 API
│   │   │   ├── docker.py             # Docker 操作 API
│   │   │   └── backup.py             # 备份管理 API
│   │   └── services/                 # 业务逻辑层
│   │       ├── instance_service.py
│   │       ├── docker_service.py
│   │       └── config_service.py     # openclaw.json 配置管理
│   ├── scripts/                      # PowerShell 脚本
│   └── data/
│       └── openclaw.db               # SQLite 数据库
├── frontend/                         # Vue3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue
│   │   │   ├── Instances.vue
│   │   │   ├── InstanceDetail.vue    # 包含配置编辑器
│   │   │   └── Backups.vue
│   │   ├── api/                      # API 接口封装
│   │   └── stores/                   # Pinia 状态管理
│   └── package.json
├── instances/                        # 实例数据目录
│   └── {instance-id}/
│       ├── data/
│       │   └── openclaw.json         # OpenClaw 配置文件 (JSON5)
│       └── logs/
└── docker-compose.template.yml
```

### 核心数据流

1. **实例创建**: 前端 → POST /api/instances → 后端执行 add-instance.ps1 → 创建目录 + 写入数据库
2. **配置管理**: 前端 → GET/PUT /api/instances/{id}/config → 读写 openclaw.json (JSON5)
3. **状态同步**: 后端定时查询 Docker 状态 → 更新数据库 → WebSocket 推送前端

## Common Commands

### 后端开发

```powershell
cd backend

# 安装依赖
uv sync

# 启动开发服务器
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 数据库初始化
uv run python -c "from app.database import init_db; init_db()"

# 添加依赖
uv add package_name
```

### 前端开发

```powershell
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### Docker 操作

```powershell
# 构建 OpenClaw 镜像
git clone https://github.com/openclaw/openclaw.git
cd openclaw
docker build -t openclaw:local -f Dockerfile .

# 查看实例容器状态
docker ps --filter "name=openclaw-"
```

## Development Guidelines

### 后端开发规范

1. **API 路由**: 统一使用 `/api` 前缀，返回标准响应格式:
   ```python
   {"code": 0, "data": {}, "message": "success"}
   ```

2. **JSON5 支持**: 配置读取使用 `pyjson5` 库，支持注释和尾逗号

3. **异步脚本执行**: 使用 `asyncio.create_subprocess_exec` 调用 PowerShell:
   ```python
   proc = await asyncio.create_subprocess_exec(
       "powershell", "-File", script_path, *args,
       stdout=asyncio.subprocess.PIPE,
       stderr=asyncio.subprocess.PIPE
   )
   ```

4. **数据库操作**: 使用 SQLAlchemy 2.0 语法，配合 FastAPI 依赖注入

### 前端开发规范

1. **组件结构**: 每个页面一个 `.vue` 文件，复杂逻辑拆分为 composables

2. **API 封装**: 使用 axios 封装请求，统一处理错误:
   ```typescript
   // api/instances.ts
   export const getInstances = () => request.get('/api/instances')
   ```

3. **配置编辑器**: 使用 Monaco Editor 或 CodeMirror 6，支持 JSON5 语法高亮

4. **状态管理**: Pinia store 按功能拆分，实例状态实时刷新

### PowerShell 脚本规范

1. **参数定义**: 使用 `[CmdletBinding()]` 和 `param()` 块
2. **错误处理**: 使用 `try/catch/finally`，退出码 0 表示成功
3. **日志输出**: 统一格式 `[INFO]`, `[WARN]`, `[ERROR]`, `[SUCCESS]`
4. **返回值**: 复杂数据返回 JSON 字符串供后端解析

## Key Features

### 实例配置管理 (openclaw.json)

- 支持 JSON5 格式（注释、尾逗号）
- Web 界面提供语法高亮编辑器
- 保存时自动验证 JSON5 语法
- 实例重启后自动加载新配置

### WebSocket 实时日志

- 前端连接 WebSocket 获取实时日志流
- 后端通过 `docker logs -f` 推送日志
- 支持按实例筛选日志

### 数据库模型

```python
# Instance 表
- id: str (主键，英文标识如 "zhangsan")
- name: str (显示名称如 "张三")
- port: int (映射端口 18789+)
- status: str (created/running/stopped/error)
- created_at: datetime
- updated_at: datetime

# Backup 表
- id: int (主键)
- filename: str
- size: int
- created_at: datetime
- instance_count: int
```

## API Endpoints

```
GET    /api/instances              # 获取所有实例列表
POST   /api/instances              # 创建新实例
GET    /api/instances/{id}         # 获取实例详情
DELETE /api/instances/{id}         # 删除实例
POST   /api/instances/{id}/start   # 启动实例
POST   /api/instances/{id}/stop    # 停止实例
POST   /api/instances/{id}/init    # 初始化实例
GET    /api/instances/{id}/logs    # 获取实例日志 (WebSocket)
GET    /api/instances/{id}/config  # 获取实例配置 (JSON5)
PUT    /api/instances/{id}/config  # 更新实例配置

GET    /api/backups                # 获取备份列表
POST   /api/backups                # 创建备份
DELETE /api/backups/{id}           # 删除备份

GET    /api/system/status          # 系统状态 (Docker 状态等)
GET    /api/system/ports           # 获取可用端口范围
```
