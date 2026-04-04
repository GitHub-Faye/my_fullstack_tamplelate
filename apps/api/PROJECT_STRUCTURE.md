# API 项目结构说明

## 项目概述

这是一个基于 **FastAPI** + **SQLModel** + **PostgreSQL** + **Redis** 构建的现代化异步后端 API 服务，采用领域驱动设计（DDD）架构风格。

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI (异步) |
| ORM | SQLModel (SQLAlchemy 2.0) |
| 数据库 | PostgreSQL 16 |
| 缓存/队列 | Redis 7 |
| 认证 | JWT (PyJWT) |
| 密码哈希 | Argon2 / Bcrypt (pwdlib) |
| 数据库迁移 | Alembic |
| 测试 | pytest (异步模式) |
| 部署 | Docker + Docker Compose |

---

## 目录结构

```
apps/api/
├── .env                          # 环境变量配置文件
├── .gitignore                    # Git 忽略规则
├── docker-compose.yml            # Docker 服务编排配置
├── main.py                       # 应用入口文件
├── main_example.py               # FastAPI 示例代码参考
├── package.json                  # npm 脚本配置（用于 monorepo）
├── pytest.ini                    # pytest 测试配置
├── app/                          # 应用主代码目录
│   ├── __init__.py
│   ├── alembic.ini               # Alembic 迁移配置
│   ├── alembic/                  # 数据库迁移脚本
│   │   ├── env.py                # 迁移环境配置
│   │   ├── README                # Alembic 说明
│   │   ├── script.py.mako        # 迁移脚本模板
│   │   └── versions/             # 迁移版本文件
│   ├── api/                      # API 路由入口层
│   │   ├── __init__.py
│   │   ├── api.md                # API 层说明文档
│   │   ├── api.py                # 主路由聚合器
│   │   └── v1/                   # API v1 版本
│   │       ├── __init__.py
│   │       └── api.py            # v1 路由注册
│   ├── core/                     # 核心基础设施层
│   │   ├── __init__.py
│   │   ├──  core.md              # 核心层说明文档
│   │   ├── config.py             # 应用配置管理
│   │   ├── database.py           # 数据库连接与会话管理
│   │   ├── events.py             # 应用事件处理
│   │   ├── logging.py            # 日志配置
│   │   ├── middleware.py         # 自定义中间件
│   │   ├── models.py             # 核心数据模型 (User, Item)
│   │   └── security.py           # 安全工具 (JWT, 密码哈希)
│   ├── domains/                  # 业务领域层
│   │   ├── domains.md            # 领域层说明文档
│   │   ├── item/                 # Item 领域模块
│   │   │   ├── repository.py     # Item 数据访问层
│   │   │   ├── router.py         # Item API 路由
│   │   │   └── schemas.py        # Item Pydantic 模型
│   │   └── user/                 # User 领域模块
│   │       ├── __init__.py
│   │       ├── dependencies.py   # 用户认证依赖注入
│   │       ├── exceptions.py     # 用户相关异常
│   │       ├── repository.py     # User 数据访问层 (CRUD)
│   │       ├── schemas.py        # User Pydantic 模型
│   │       ├── utils.py          # 用户工具函数
│   │       └── router/           # User 路由子模块
│   │           ├── __init__.py
│   │           ├── login.py      # 登录/认证路由
│   │           └── user.py       # 用户管理路由
│   └── tasks/                    # 异步任务队列 (Celery)
│       └── tasks.md              # 任务队列说明文档
└── tests/                        # 测试目录
    └── tests.md                  # 测试说明文档
```

---

## 架构分层说明

### 1. API 层 (`app/api/`)

**职责**: 管理 API 路由入口和版本控制

| 文件 | 说明 |
|------|------|
| `api.py` | 主路由聚合器，包含所有版本路由 |
| `v1/api.py` | API v1 版本路由注册，按领域模块组织 |

**路由注册流程**:
```
main.py → app/api/api.py → app/api/v1/api.py → domains/*/router/*.py
```

### 2. Core 层 (`app/core/`)

**职责**: 基础设施和横切关注点，不依赖业务逻辑

| 文件 | 说明 |
|------|------|
| `config.py` | Pydantic Settings 配置管理，支持 `.env` 文件 |
| `database.py` | SQLAlchemy 异步引擎、会话工厂、数据库初始化 |
| `models.py` | SQLModel 核心模型：User、Item 及关系定义 |
| `security.py` | JWT 令牌生成/验证、密码哈希 (Argon2/Bcrypt) |
| `middleware.py` | 自定义中间件 (请求处理时间统计) |

### 3. Domains 层 (`app/domains/`)

**职责**: 业务领域逻辑，按领域模块组织

#### User 领域 (`domains/user/`)

| 文件 | 说明 |
|------|------|
| `schemas.py` | Pydantic 模型：UserBase, UserCreate, UserPublic, Token 等 |
| `repository.py` | 数据访问层：create_user, update_user, authenticate 等 |
| `dependencies.py` | FastAPI 依赖：SessionDep, CurrentUser, get_current_active_superuser |
| `utils.py` | 邮件发送、密码重置令牌生成等工具函数 |
| `router/login.py` | 登录相关端点：/login/access-token, /reset-password |
| `router/user.py` | 用户管理端点：CRUD、注册、密码修改等 |

#### Item 领域 (`domains/item/`)

| 文件 | 说明 |
|------|------|
| `schemas.py` | Pydantic 模型：ItemBase, ItemCreate, ItemPublic 等 |
| `repository.py` | Item 数据访问层 |
| `router.py` | Item CRUD 端点，支持超管查看全部 |

### 4. Tasks 层 (`app/tasks/`)

**职责**: 异步任务队列（预留 Celery 扩展）

---

## 数据模型关系

```
┌─────────────┐         ┌─────────────┐
│    User     │◄───────►│    Item     │
├─────────────┤   1:N   ├─────────────┤
│ id (PK)     │         │ id (PK)     │
│ email       │         │ title       │
│ hashed_pass │         │ description │
│ is_active   │         │ owner_id FK │
│ is_superuser│         │ created_at  │
│ full_name   │         └─────────────┘
│ created_at  │
└─────────────┘
```

- User 与 Item 为一对多关系
- 删除 User 级联删除其所有 Item (`cascade_delete=True`)

---

## API 端点概览

### 认证端点 (`/api/v1/login/*`)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/login/access-token` | OAuth2 登录获取 JWT |
| POST | `/login/test-token` | 验证令牌有效性 |
| POST | `/reset-password/` | 重置密码 |

### 用户端点 (`/api/v1/users/*`)

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/users/` | 超管 | 获取用户列表（分页） |
| POST | `/users/` | 超管 | 创建用户 |
| GET | `/users/me` | 登录用户 | 获取当前用户信息 |
| PATCH | `/users/me` | 登录用户 | 更新当前用户信息 |
| PATCH | `/users/me/password` | 登录用户 | 修改密码 |
| DELETE | `/users/me` | 登录用户 | 删除自己账户 |
| POST | `/users/signup` | 公开 | 用户注册 |
| GET | `/users/{id}` | 登录用户 | 获取指定用户信息 |
| PATCH | `/users/{id}` | 超管 | 更新指定用户 |
| DELETE | `/users/{id}` | 超管 | 删除指定用户 |

### Item 端点 (`/api/v1/items/*`)

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/items/` | 登录用户 | 获取 Item 列表（超管看全部） |
| POST | `/items/` | 登录用户 | 创建 Item |
| GET | `/items/{id}` | 登录用户 | 获取指定 Item |
| PUT | `/items/{id}` | 登录用户 | 更新 Item |
| DELETE | `/items/{id}` | 登录用户 | 删除 Item |

---

## 配置说明

### 环境变量 (`.env`)

| 变量 | 说明 |
|------|------|
| `DOMAIN` | 项目域名 |
| `FRONTEND_HOST` | 前端应用地址 |
| `ENVIRONMENT` | 运行环境 (local/staging/production) |
| `SECRET_KEY` | JWT 签名密钥 |
| `DATABASE_URL` | PostgreSQL 连接字符串 |
| `REDIS_URL` | Redis 连接字符串 |
| `SMTP_*` | 邮件服务配置 |
| `FIRST_SUPERUSER` | 初始超管邮箱 |
| `FIRST_SUPERUSER_PASSWORD` | 初始超管密码 |

---

## 开发命令

```bash
# 启动开发服务器
fastapi dev

# 启动生产服务器
fastapi start

# 运行测试
pytest

# 数据库迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head

# Docker 启动依赖服务
docker-compose up -d
```

---

## 安全特性

1. **密码安全**: Argon2 哈希，支持自动升级算法
2. **JWT 认证**: HS256 签名，可配置过期时间
3. **时序攻击防护**: 用户不存在时执行虚拟密码验证
4. **CORS 控制**: 可配置的跨域源列表
5. **权限分级**: 普通用户 / 超级用户权限隔离
6. **密钥检查**: 生产环境强制检查默认密钥

---

## 扩展建议

- **任务队列**: 在 `app/tasks/` 集成 Celery
- **缓存层**: 使用 Redis 缓存热点数据
- **文件存储**: 添加对象存储服务 (MinIO/S3)
- **监控**: 集成 Sentry 错误追踪
- **日志**: 结构化日志输出到 ELK/Loki
