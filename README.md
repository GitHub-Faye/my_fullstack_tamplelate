# My Fullstack Template

全栈开发模板，基于 **FastAPI + Next.js + SQLite + TanStack Query** 的现代化 Monorepo 架构。

> **定位**：这是一个「起始项目模板」，任何新业务域接入时都遵循同一套开发规范。
> 后端以 `user` / `role` 两个业务域为参考范例，前端以 `item` 为参考范例，模板已内置：
> 统一的三层架构、RBAC 权限体系（Scope）、错误体系、分页协议、前后端契约同步链路。

---

## 📋 项目架构总览

```
my_fullstack_tamplelate/
├── apps/
│   ├── api/          # FastAPI 后端 (Python)
│   ├── web/          # Next.js 前端 (TypeScript/React)
│   └── docs/         # 文档站点
├── packages/
│   ├── contracts/    # 共享业务契约 (错误码/Scope/分页)
│   ├── sdk/          # OpenAPI 自动生成 SDK + React Query
│   ├── ui/           # 共享 UI 组件 (Button/Card/Code)
│   ├── eslint-config/ # 共享 ESLint 配置
│   └── typescript-config/ # 共享 TS 配置
└── pnpm-workspace.yaml  # Monorepo 工作区定义
```

| 层 | 技术栈 | 路径 |
|----|--------|------|
| **后端** | FastAPI + SQLModel + SQLite | [`apps/api/`](apps/api/) |
| **前端** | Next.js + React + TanStack Query + shadcn/ui | [`apps/web/`](apps/web/) |
| **SDK** | OpenAPI 自动生成客户端 + React Query Hooks | [`packages/sdk/`](packages/sdk/sdk.md) |
| **契约** | 共享错误码/Scope/分页协议 | [`packages/contracts/`](packages/contracts/contracts.md) |
| **UI** | 共享 React 组件 | [`packages/ui/`](packages/ui/) |
| **文档** | 文档站 | [`apps/docs/`](apps/docs/) |

**数据流：** `前端 (Next.js)` → `SDK (@repo/sdk)` → `API (FastAPI)` → `SQLite`

---

## 🚀 首次启动（5 步）

### 1. 安装依赖

```bash
# 安装 Node 依赖（根目录）
pnpm install

# 安装 Python 依赖
uv venv --python 3.11
uv sync
```

### 2. 准备数据库

本项目默认使用 **SQLite**（文件数据库），无需 Docker 或外部数据库服务。
启动时如数据库文件不存在会自动创建。

> 如需使用 MySQL / PostgreSQL，在 [`apps/api/.env`](apps/api/.env) 中设置 `DATABASE_URL` 即可，例如：
> `DATABASE_URL=mysql+asyncmy://user:pass@host:3306/dbname`
> `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname`

### 3. 数据库迁移

```bash
cd apps/api
uv run alembic upgrade head
```

模型定义在 [`app/core/models.py`](apps/api/app/core/models.py)，迁移配置在 [`migrations/env.py`](apps/api/migrations/env.py)。

### 4. 启动后端

```bash
cd apps/api
pnpm dev     # fastapi dev 热重载
```

后端默认运行在 `http://localhost:8000`，API 文档：`http://localhost:8000/docs`

### 5. 启动前端

```bash
cd apps/web
pnpm dev     # next dev --port 3000
```

前端默认运行在 `http://localhost:3000`

---

## 🏗️ 后端开发规范（核心：三层架构）

> 这是模板最重要的部分——**任何新业务域都必须遵循同一套分层规范**。
> 参考范例：`apps/api/app/domains/user/` 与 `apps/api/app/domains/role/`。

### 目录结构约定

每个业务域一个目录 `domains/<name>/`，固定 6 个文件：

```
domains/<name>/
├── __init__.py     # 空文件，包标记
├── schemas.py      # Pydantic 请求/响应 DTO（XxxCreate / XxxUpdate / XxxPublic / XxxsPublic）
├── repository.py   # 数据库 CRUD（只 flush，不 commit）
├── service.py      # 业务编排（唯一持有事务 commit/rollback 的层）
├── responses.py    # Public 响应组装（附带批量 scope 查询）
└── router.py       # API 路由定义（依赖注入 scope 校验）
```

### 分层职责与规则

| 层 | 职责 | 硬性规则 |
|----|------|----------|
| **router** | 接收 HTTP 请求、参数校验、依赖注入、返回组装好的响应 | 不写业务逻辑；scope 校验用 `Depends(require_scope(...))` |
| **service** | 业务编排：唯一性预检 → 调 repository → commit/rollback | **事务归属方**；所有写操作用 `try/except IntegrityError` 兜底并发冲突 |
| **repository** | SQLModel 增删改查、批量查询 | 只 `flush()` 不 `commit()`；单一职责的查询函数 |
| **responses** | 把模型组装为 Public DTO，批量查询 scope | 避免逐条 N+1 查询 scope |

**事务管理铁律：**
```python
# service.py —— 唯一合法持有 commit 的地方
async def create_xxx(*, session, xxx_in) -> Xxx:
    if await repository.get_xxx_by_name(session, name=xxx_in.name):
        raise_xxx_already_exists(...)
    try:
        obj = await repository.create_xxx(session=session, xxx_in=xxx_in)
        await session.commit()
        return obj
    except IntegrityError:
        await session.rollback()          # 并发唯一性兜底
        raise_xxx_already_exists(...)
```

### 错误体系

统一在 [`app/core/errors.py`](apps/api/app/core/errors.py) 中扩展，禁止散落 `HTTPException`：

1. 在 `ErrorCode` 枚举中新增错误码（格式 `DOMAIN_ACTION_DETAIL`）
2. 在 `ERROR_STATUS_MAP` 映射 HTTP 状态码
3. 在 `DEFAULT_ERROR_MESSAGES` 写默认消息
4. （可选）添加 `raise_xxx(...)` 工厂函数

```python
class ErrorCode(str, Enum):
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"          # 新增
    ORDER_ALREADY_EXISTS = "ORDER_ALREADY_EXISTS"

ERROR_STATUS_MAP[ErrorCode.ORDER_NOT_FOUND] = status.HTTP_404_NOT_FOUND

def raise_order_not_found(detail=None) -> NoReturn:
    raise BusinessException(code=ErrorCode.ORDER_NOT_FOUND, detail=detail)
```

### Scope 权限体系

统一在 [`app/core/scopes.py`](apps/api/app/core/scopes.py) 中扩展：

```python
class OrderScope(str, Enum):
    READ = "order:read"
    CREATE = "order:create"
    UPDATE = "order:update"
    DELETE = "order:delete"
    ADMIN = "order:admin"

ALL_ORDER_SCOPES = [OrderScope.READ, OrderScope.CREATE, OrderScope.UPDATE, OrderScope.DELETE, OrderScope.ADMIN]
ALL_SCOPES = ALL_USER_SCOPES + ALL_ROLE_SCOPES + ALL_ORDER_SCOPES   # 记得加入总集合！
```

路由中使用三个依赖函数（定义在 [`app/core/dependencies.py`](apps/api/app/core/dependencies.py)）：

```python
from app.core.dependencies import require_scope, require_any_scope, require_all_scopes

@router.get("/", response_model=OrdersPublic)
async def read_orders(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
    _: Annotated[None, Depends(require_scope(OrderScope.READ))],
) -> Any: ...

@router.delete("/{order_id}")
async def delete_order(
    session: SessionDep,
    order_id: uuid.UUID,
    _: Annotated[None, Depends(require_any_scope(OrderScope.ADMIN, OrderScope.DELETE))],
) -> Message: ...
```

> **超管天然拥有全部 scope**（`is_superuser=True`），无需特判。预置角色（viewer/editor/admin）在 `init_roles_and_scopes()` 启动时初始化，不可修改/删除。

---

## ➕ 新增一个业务域的完整流程

> 以新增 **订单（Order）** 域为例。按顺序执行以下步骤。

### 第 1 步：定义数据库模型

在 [`apps/api/app/core/models.py`](apps/api/app/core/models.py) 添加模型：

```python
class Order(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=50)
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)
    )
```

### 第 2 步：生成数据库迁移

```bash
cd apps/api
uv run alembic revision --autogenerate -m "add order table"
uv run alembic upgrade head
```

### 第 3 步：创建 Domain 模块（6 个文件）

复制 `domains/role/` 的骨架，逐文件改造：

| 文件 | 核心内容 |
|------|----------|
| `schemas.py` | `OrderCreate` / `OrderUpdate` / `OrderPublic`（含 `scopes` 或业务字段）/ `OrdersPublic(PaginatedResponse[OrderPublic])` |
| `repository.py` | `get_order` / `get_orders`（分页+count）/ `create_order`（flush）/ `update_order` / `delete_order` |
| `service.py` | 唯一性预检 → repository → `commit`；`IntegrityError` 兜底 |
| `responses.py` | `order_public` / `orders_public`（批量 scope 查询） |
| `router.py` | RESTful 路由 + `require_scope(OrderScope.X)` |
| `__init__.py` | 空文件 |

> ⚠️ SQLModel `Relationship` 字段类型必须用 `Optional["Xxx"]` 写法，**不能用 `"Xxx | None"`**（SQLAlchemy 无法解析 union 语法字符串注解）。

### 第 4 步：注册 Scope（两个文件）

- [`app/core/scopes.py`](apps/api/app/core/scopes.py)：新增 `OrderScope` 枚举 + `ALL_ORDER_SCOPES` + 加入 `ALL_SCOPES`
- [`packages/contracts/src/scopes.ts`](packages/contracts/src/scopes.ts)：同步新增 `OrderScope` 常量 + `ALL_ORDER_SCOPES` + 更新 `ScopeType` 联合类型 + `ALL_SCOPES` + `DEFAULT_ROLE_SCOPES`

> ⚠️ **前后端必须保持 scope 字符串一致**，这是契约同步的硬约束。

### 第 5 步：注册路由

在 [`apps/api/app/api/v1/api.py`](apps/api/app/api/v1/api.py) 添加：

```python
from app.domains.order.router import router as order_router

router.include_router(order_router, prefix="/orders", tags=["orders"])
```

### 第 6 步：生成 SDK

```bash
cd packages/sdk
pnpm generate     # 从 OpenAPI 自动生成客户端 + React Query Hooks
```

### 第 7 步：编写测试

在 [`apps/api/tests/`](apps/api/tests/) 新建 `test_orders.py`，复用现有测试夹具（`db_session` / `client` / `authorized_client` / `superuser_client`）：

```python
@pytest.mark.asyncio
async def test_create_order_success(superuser_client: AsyncClient):
    response = await superuser_client.post(
        "/v1/orders/", json={"name": "ORD-1"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "ORD-1"
```

运行测试：

```bash
cd apps/api && pnpm test    # 或 pytest
```

### 第 8 步：前端开发（可选）

按 [`apps/web/features/item/`](apps/web/features/item/) 模板创建 `features/order/`：

```
features/order/
├── index.ts
├── api/
│   ├── index.ts
│   ├── client/             # 客户端组件数据获取
│   │   ├── index.ts
│   │   └── queries.ts      # TanStack Query Hooks
│   └── server/             # 服务端组件数据获取
│       ├── index.ts
│       └── queries.ts
├── client/                 # 客户端组件（Table / Form / Detail）
├── schemas/                # 前端业务类型
└── server/                 # 服务端组件（List / Detail）
```

在 [`apps/web/components/navbar.tsx`](apps/web/components/navbar.tsx) 添加导航项，并按 scope 控制页面可见性：

```tsx
import { OrderScope, hasScope } from '@repo/contracts/scopes';

const userScopes = user?.scopes ?? [];
if (!hasScope(userScopes, OrderScope.READ)) return null; // 无权限不显示
```

---

## 🔐 权限系统（RBAC）设计

### 数据模型

```
User ────(多对多)──── Role ────(一对多)──── Scope
```

| 表 | 用途 | 定义位置 |
|----|------|----------|
| `User` | 用户（含 `is_superuser` 标记） | [`app/core/models.py`](apps/api/app/core/models.py) |
| `Role` | 角色（viewer / editor / admin） | 同上 |
| `UserRole` | 用户-角色多对多关联 | 同上 |
| `RoleScopeModel` | 角色-权限关联（`scope` 字符串） | 同上 |

### 权限判定

- **scope 命名**：统一 `资源:操作` 格式（`order:read`、`order:admin`）
- **超管**：`is_superuser=True` 自动拥有全部 scope（`get_user_scopes()` 实现，见 [`dependencies.py`](apps/api/app/core/dependencies.py)）
- **角色**：用户经角色获得 scope；预置角色在 `init_roles_and_scopes()` 启动时初始化（[`database.py`](apps/api/app/core/database.py)）
- **预置角色不可修改/删除**：`BUILTIN_ROLES = ("viewer", "editor", "admin")`

### 三种权限检查粒度

| 函数 | 语义 | 示例 |
|------|------|------|
| `require_scope` | 必须拥有该 scope | `require_scope(OrderScope.READ)` |
| `require_any_scope` | 满足任意一个即可 | `require_any_scope(OrderScope.ADMIN, OrderScope.DELETE)` |
| `require_all_scopes` | 必须全部拥有 | `require_all_scopes(OrderScope.READ, SystemScope.READ)` |

---

## 🔄 前后端契约同步

新增错误码 / Scope / 分页改动时，**必须同步**以下文件：

| 后端 | 前端契约包 |
|------|-----------|
| [`apps/api/app/core/errors.py`](apps/api/app/core/errors.py) | [`packages/contracts/src/errors.ts`](packages/contracts/src/errors.ts) |
| [`apps/api/app/core/scopes.py`](apps/api/app/core/scopes.py) | [`packages/contracts/src/scopes.ts`](packages/contracts/src/scopes.ts) |
| [`apps/api/app/core/schemas.py`](apps/api/app/core/schemas.py)（分页协议） | [`packages/contracts/src/pagination.ts`](packages/contracts/src/pagination.ts) |

> ⚠️ 后端 `scopes.py` 与前端 `scopes.ts` 是**单一事实源的两个镜像**，字符串必须逐字一致。
> 验证方法：运行 `cd apps/api && pnpm test` 确认后端行为，运行 `cd packages/contracts && pnpm lint && pnpm test` 确认前端契约。

---

## 📐 架构约定速查

### 后端约定

| 约定 | 说明 |
|------|------|
| **Domain 划分** | 每个业务域一个目录：`domains/<name>/`（6 个固定文件） |
| **三层架构** | router → service → repository，禁止跨层调用 |
| **事务归属** | service 层 commit/rollback，repository 层仅 flush |
| **路由注册** | 统一在 [`app/api/v1/api.py`](apps/api/app/api/v1/api.py) 注册 |
| **权限控制** | `require_scope` / `require_any_scope` / `require_all_scopes` |
| **错误处理** | 统一 [`app/core/errors.py`](apps/api/app/core/errors.py) 中的 ErrorCode + 工厂函数 |
| **异步优先** | 所有数据库操作使用 SQLModel 异步接口 |
| **自动迁移** | 模型修改后运行 `alembic revision --autogenerate` |
| **定时/后台任务** | 暂未接入（Celery 已移除），后续需要可重新引入 |

### 前端约定

| 约定 | 说明 |
|------|------|
| **Feature 划分** | 每个业务域一个目录：`features/<name>/` |
| **客户端/服务端** | 明确区分 `client/` 和 `server/` 子目录 |
| **API 调用** | 客户端通过 TanStack Query + SDK，服务端通过 SDK 直调 |
| **UI 组件** | 优先使用 [`components/ui/`](apps/web/components/ui/) 中的 shadcn/ui 组件 |
| **表单** | 使用 `react-hook-form` + `zod` 校验 |
| **主题** | 使用 `next-themes` 暗色模式 |
| **Auth** | JWT Token 存储在 Cookie 中，[`middleware.ts`](apps/web/middleware.ts) 处理路由保护 |

---

## ⚡ 常用命令速查

```bash
# ── 根目录（Monorepo）──
pnpm dev              # 同时启动所有应用
pnpm build            # 构建所有包
pnpm test             # 运行所有测试
pnpm lint             # 代码检查
pnpm check-types      # TypeScript 类型检查

# ── 后端 ──
cd apps/api
pnpm dev              # fastapi dev（热重载）
pnpm test             # pytest
uv run alembic upgrade head  # 数据库迁移
uv run alembic revision --autogenerate -m "描述"  # 生成迁移

# ── 前端 ──
cd apps/web
pnpm dev              # next dev（热重载）
pnpm test             # vitest
pnpm test:coverage    # 测试覆盖率

# ── SDK ──
cd packages/sdk
pnpm generate         # 从 OpenAPI 重新生成 SDK
```

---

## 📁 项目结构索引

| 路径 | 说明 |
|------|------|
| [`apps/api/app/core/`](apps/api/app/core/) | 后端核心（配置、数据库、安全、中间件、日志、错误、scope） |
| [`apps/api/app/domains/`](apps/api/app/domains/) | 业务域（user、role）——**新业务域参考范例** |
| [`apps/api/app/api/v1/`](apps/api/app/api/v1/) | API 路由注册入口 |
| [`apps/api/migrations/`](apps/api/migrations/) | Alembic 数据库迁移 |
| [`apps/api/tests/`](apps/api/tests/) | 后端测试（pytest + pytest-asyncio） |
| [`apps/web/app/`](apps/web/app/) | Next.js 页面路由 |
| [`apps/web/components/`](apps/web/components/) | 全局 UI 组件（navbar、providers、shadcn/ui） |
| [`apps/web/features/`](apps/web/features/) | 前端业务模块——**新前端业务参考范例** |
| [`apps/web/lib/`](apps/web/lib/) | 工具函数（API SDK 客户端、utils） |
| [`packages/contracts/src/`](packages/contracts/src/) | 共享契约（错误码、Scope、分页、常量） |
| [`packages/sdk/src/`](packages/sdk/src/) | OpenAPI 自动生成 SDK |
| [`packages/ui/src/`](packages/ui/src/) | 共享 UI 组件 |
