# Core 目录

`app/core/` 是应用程序的基础设施层，包含所有核心配置和基础服务。这些模块为整个应用提供底层支持，不依赖于业务逻辑。

## 目录作用

作为 FastAPI 应用的基础设施层，负责：
- 应用配置管理（环境变量、数据库连接等）
- 数据库连接和会话管理
- 安全认证和密码处理
- 结构化日志记录
- 中间件组件
- 基础数据模型定义

## 文件说明

### `__init__.py`
空文件，标记这是一个 Python 包。

### `config.py`
**应用配置管理模块**

使用 Pydantic v2 的 `BaseSettings` 实现，自动从 `.env` 文件和环境变量加载配置。

主要功能：
- 从 `apps/api/.env` 文件加载环境变量
- 定义所有应用配置项（API、安全、数据库、邮件等）
- 提供 `get_settings()` 单例函数获取配置
- 包含 CORS 源解析工具函数
- 安全验证：检查关键密钥是否使用了默认值

关键配置项：
- `API_V1_STR`: API 版本前缀
- `SECRET_KEY`: JWT 签名密钥
- `SQLALCHEMY_DATABASE_URI`: 数据库连接 URI
- `CORS_ALLOW_ORIGINS`: 跨域允许源列表
- `SMTP_*`: 邮件服务器配置
- `FIRST_SUPERUSER`: 初始超级管理员账户

### `database.py`
**数据库连接和会话管理模块**

基于 SQLModel 和 SQLAlchemy 2.0 的异步数据库支持。

主要功能：
- 创建异步数据库引擎（使用 `create_async_engine`）
- 配置异步会话工厂（`AsyncSessionLocal`）
- 提供 `get_db()` 依赖函数用于 FastAPI 依赖注入
- 提供 `init_db()` 函数初始化数据库（创建表）

技术栈：
- SQLModel: ORM 模型基类
- SQLAlchemy 2.0: 异步引擎和会话
- asyncpg: PostgreSQL 异步驱动

### `security.py`
**安全认证和密码处理模块**

处理用户认证、密码哈希和 JWT 令牌。

主要功能：
- 密码哈希：使用 Argon2（首选）和 Bcrypt 双算法
- 密码验证：支持自动哈希升级（从 Bcrypt 升级到 Argon2）
- JWT 令牌生成和验证
- OAuth2 密码流配置

关键组件：
- `password_hash`: PasswordHash 实例，配置 Argon2 + Bcrypt
- `reusable_oauth2`: OAuth2PasswordBearer 实例，用于 FastAPI 安全依赖
- `create_access_token()`: 生成 JWT 访问令牌
- `verify_password()`: 验证密码并支持哈希升级
- `get_password_hash()`: 生成密码哈希

### `logging.py`
**结构化日志配置模块**

使用 `structlog` 提供统一的结构化日志系统。

主要功能：
- 开发环境：彩色控制台输出
- 生产环境：JSON 格式输出
- 与标准库 `logging` 桥接
- 自动添加应用信息（app_name, environment, service）
- 支持 FastAPI 和 Celery 集成

关键函数：
- `configure_logging()`: 配置日志系统（在应用启动时调用）
- `get_logger(name)`: 获取结构化日志记录器
- `add_app_info`: 处理器，添加应用元数据到日志事件

### `middleware.py`
**FastAPI 中间件模块**

自定义 HTTP 中间件，处理请求生命周期。

当前中间件：
- `ProcessTimeMiddleware`: 请求处理时间中间件
  - 生成唯一请求 ID
  - 记录请求开始和完成日志
  - 添加 `X-Process-Time` 响应头（处理时间，秒）
  - 添加 `X-Request-ID` 响应头
  - 捕获并记录异常

### `models.py`
**基础数据模型定义**

使用 SQLModel 定义数据库表模型和 Pydantic 模式。

定义模型：
- `UserBase` / `User`: 用户模型
  - 字段：email, is_active, is_superuser, full_name, hashed_password, created_at
  - 关系：items（一对多关联 Item）
- `ItemBase` / `Item`: 项目模型
  - 字段：title, description, created_at, owner_id
  - 关系：owner（多对一关联 User）

特性：
- 使用 UUID 作为主键
- UTC 时间戳自动设置
- 级联删除配置（删除用户时删除关联项目）

### `events.py`
**应用事件处理模块**

当前为空文件，预留用于：
- 应用启动事件（startup events）
- 应用关闭事件（shutdown events）
- 生命周期管理

## 使用示例

```python
# 获取配置
from app.core.config import get_settings
settings = get_settings()

# 获取数据库会话
from app.core.database import get_db
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    pass

# 获取日志记录器
from app.core.logging import get_logger
logger = get_logger(__name__)
logger.info("user_action", user_id=123)

# 密码处理
from app.core.security import get_password_hash, verify_password
hashed = get_password_hash("password")
is_valid, new_hash = verify_password("password", hashed)

# JWT 令牌
from app.core.security import create_access_token
from datetime import timedelta
token = create_access_token(user_id, timedelta(hours=1))
```

## 依赖关系

```
config.py (基础配置)
    ↓
database.py, security.py, logging.py (依赖配置)
    ↓
middleware.py, models.py (依赖上述模块)
```

## 注意事项

1. **配置安全**：生产环境必须修改默认密钥（`SECRET_KEY`, `POSTGRES_PASSWORD`, `FIRST_SUPERUSER_PASSWORD`）
2. **数据库**：使用异步引擎，所有数据库操作需使用 `async/await`
3. **日志**：在应用启动时调用 `configure_logging()` 初始化日志系统
4. **模型**：修改模型后需要运行 Alembic 迁移更新数据库结构
