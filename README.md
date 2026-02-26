# ClawMultiDeploy

用于在 Windows 环境下通过 Docker 部署多个完全隔离的 OpenClaw 实例，提供可视化 Web 界面实现便捷的多实例管理与运维。

## 项目目标

为公司同事提供独立的 OpenClaw AI 网关实例，通过 Web 界面实现：
- 一键创建、启动、停止、删除实例
- 实时查看实例状态和日志
- 批量备份所有实例数据
- 支持动态扩展实例数量

## 技术栈

### 后端
- **框架**：FastAPI (Python)
- **数据库**：SQLite
- **包管理**：uv
- **任务执行**：PowerShell 脚本集成

### 前端
- **框架**：Vue 3 + TypeScript
- **构建工具**：Vite
- **UI 组件**：Element Plus
- **状态管理**：Pinia

### 基础设施
- **容器化**：Docker, Docker Compose
- **目标应用**：[OpenClaw](https://github.com/openclaw/openclaw.git)

## 架构设计

### 目录结构

```
openclaw-deploy/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── models.py                 # SQLite 数据模型
│   │   ├── database.py               # 数据库连接
│   │   ├── schemas.py                # Pydantic 模型
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── instances.py          # 实例管理 API
│   │   │   ├── docker.py             # Docker 操作 API
│   │   │   └── backup.py             # 备份管理 API
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── instance_service.py   # 实例业务逻辑
│   │       ├── docker_service.py     # Docker 操作封装
│   │       └── powershell_service.py # PowerShell 调用
│   ├── scripts/                      # 后端调用的脚本
│   │   ├── add-instance.ps1
│   │   ├── start-instance.ps1
│   │   ├── stop-instance.ps1
│   │   ├── remove-instance.ps1
│   │   ├── backup-instances.ps1
│   │   └── get-logs.ps1
│   ├── data/                         # 数据目录
│   │   └── openclaw.db               # SQLite 数据库
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── components/               # 公共组件
│   │   ├── views/                    # 页面视图
│   │   │   ├── Dashboard.vue         # 仪表盘
│   │   │   ├── Instances.vue         # 实例列表
│   │   │   ├── InstanceDetail.vue    # 实例详情
│   │   │   └── Backups.vue           # 备份管理
│   │   ├── stores/                   # Pinia 状态管理
│   │   ├── api/                      # API 接口封装
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.ts
├── instances/                        # 实例数据目录（自动生成）
│   └── {instance-id}/
│       ├── data/                     # 映射到 /root/.openclaw
│       │   └── openclaw.json         # OpenClaw 配置文件（JSON5 格式）
│       └── logs/                     # 映射到 /var/log/openclaw
├── backup/                           # 备份文件目录
├── docker-compose.template.yml       # Docker Compose 模板
└── README.md
```

## 核心设计

### 1. 数据库模型 (SQLite)

```python
# Instance 表
- id: str (主键，实例唯一标识)
- name: str (显示名称)
- port: int (映射端口)
- status: str (状态: created, running, stopped, error)
- created_at: datetime
- updated_at: datetime

# Backup 表
- id: int (主键)
- filename: str (备份文件名)
- size: int (文件大小)
- created_at: datetime
- instance_count: int (包含实例数)
```

### 2. 后端 API 设计

```
GET    /api/instances              # 获取所有实例列表
POST   /api/instances              # 创建新实例
GET    /api/instances/{id}         # 获取实例详情
DELETE /api/instances/{id}         # 删除实例
POST   /api/instances/{id}/start   # 启动实例
POST   /api/instances/{id}/stop    # 停止实例
POST   /api/instances/{id}/init    # 初始化实例
GET    /api/instances/{id}/logs    # 获取实例日志
GET    /api/instances/{id}/config  # 获取实例配置 (openclaw.json)
PUT    /api/instances/{id}/config  # 更新实例配置

GET    /api/backups                # 获取备份列表
POST   /api/backups                # 创建备份
DELETE /api/backups/{id}           # 删除备份
POST   /api/backups/{id}/restore   # 恢复备份

GET    /api/system/status          # 系统状态（Docker 运行状态等）
```

### 3. 端口分配策略

- 起始端口：18789
- 分配规则：`port = basePort + max_port_in_db`
- 自动检测已被占用的端口

### 4. Docker Compose 动态生成

后端根据数据库中的实例记录，从模板动态生成 `docker-compose.yml`：

```yaml
# docker-compose.template.yml
services:
  {% for instance in instances %}
  {{ instance.id }}:
    image: openclaw:local
    container_name: openclaw-{{ instance.id }}
    ports:
      - "{{ instance.port }}:18789"
    volumes:
      - ../instances/{{ instance.id }}/data:/root/.openclaw
      - ../instances/{{ instance.id }}/logs:/var/log/openclaw
    environment:
      - TZ=Asia/Shanghai
      - LANG=C.UTF-8
    restart: unless-stopped
  {% endfor %}
```

## 使用流程

### 1. 环境准备

```powershell
# 安装 uv (Python 包管理器)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装 Node.js (如果尚未安装)
# 从 https://nodejs.org/ 下载安装
```

### 2. 构建 OpenClaw 镜像

```powershell
# 克隆 OpenClaw 仓库
git clone https://github.com/openclaw/openclaw.git

# 构建镜像
cd openclaw
docker build -t openclaw:local -f Dockerfile .
cd ..
```

### 3. 启动后端服务

```powershell
cd backend

# 安装依赖
uv sync

# 初始化数据库
uv run python -c "from app.database import init_db; init_db()"

# 启动服务
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 文档：http://localhost:8000/docs

### 4. 启动前端服务

```powershell
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端界面：http://localhost:5173

### 5. 实例配置管理

每个实例拥有独立的 OpenClaw 配置文件 `instances/{id}/data/openclaw.json`，支持 JSON5 格式（允许注释和尾逗号）。

**配置编辑流程**：
1. 前端提供配置编辑器（支持 JSON5 语法高亮）
2. 后端读取/保存配置文件
3. 实例重启后自动加载新配置

**默认配置模板**：
```json5
{
    // OpenClaw 网关配置
    "gateway": {
        "mode": "local",
        "token": "",
        "port": 18789
    },
    // 智能体配置
    "agents": {
        "defaults": {
            "model": "gpt-4",
            "sandbox": {
                "mode": "non-main",
                "scope": "agent"
            }
        }
    },
    // 渠道配置
    "channels": [],
    // 工具配置
    "tools": {
        "defaults": ["*"]
    }
}
```

1. 打开浏览器访问 http://localhost:5173
2. 在"实例管理"页面点击"创建实例"
3. 输入实例 ID（如 `zhangsan`）和显示名称（如 `张三`）
4. 点击"启动"按钮启动实例
5. 点击"初始化"完成 OpenClaw 配置
6. 访问 http://localhost:18789 使用 OpenClaw

## 功能说明

### 仪表盘

- 显示实例总数、运行中数量、停止数量
- 系统资源使用情况（Docker 状态）
- 快捷操作入口

### 实例管理

- **创建实例**：输入 ID 和名称，自动分配端口，生成目录结构
- **启动/停止**：控制实例运行状态
- **配置编辑**：编辑 `openclaw.json` 配置文件（JSON5 格式，支持注释和尾逗号）
- **查看日志**：实时查看容器日志
- **删除实例**：可选保留或删除数据
- **访问地址**：显示每个实例的访问 URL

### 备份管理

- **创建备份**：停止所有实例，打包数据，自动重启
- **下载备份**：下载备份文件到本地
- **恢复备份**：从备份文件恢复实例数据
- **删除备份**：清理过期备份

## 开发说明

### 后端开发

```powershell
cd backend

# 添加依赖
uv add package_name

# 格式化代码
uv run ruff format .

# 运行测试
uv run pytest
```

### 前端开发

```powershell
cd frontend

# 添加依赖
npm install package_name

# 类型检查
npm run type-check

# 构建生产版本
npm run build
```

## 注意事项

1. **Docker Desktop**：确保已安装并运行
2. **端口占用**：确保 18789+ 端口范围未被占用
3. **PowerShell 执行策略**：可能需要设置为 RemoteSigned
4. **磁盘空间**：每个实例需要独立的数据和日志存储空间

## 技术要点

### 后端关键技术

1. **异步调用 PowerShell**：使用 `asyncio.create_subprocess_exec` 异步执行脚本
2. **WebSocket 日志推送**：实时推送容器日志到前端
3. **数据库迁移**：使用 Alembic 管理数据库版本

### 前端关键技术

1. **实时日志**：使用 WebSocket 连接后端，实时显示日志
2. **状态管理**：使用 Pinia 管理实例状态，支持实时刷新
3. **路由权限**：简单的路由守卫控制页面访问

---

**当前版本：v1.0.0（开发中）**
