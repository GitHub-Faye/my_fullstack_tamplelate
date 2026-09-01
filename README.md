# My Fullstack Template

全栈开发模板，基于 **FastAPI + Next.js + SQLite + TanStack Query** 的现代化 Monorepo 架构。

> **定位**：这是一个「起始项目模板」，任何新业务域接入时都遵循同一套开发规范。
> 后端以 `user` / `role` 两个业务域为参考范例，前端以 `features/user` / `features/role` 为参考范例，模板已内置：
> 统一的三层架构、RBAC 权限体系（Scope）、错误体系、分页协议、前后端契约同步链路。

---

## 📋 项目架构总览

```
my_fullstack_tamplelate/
├── apps/
│   ├── api/          # FastAPI 后端 (Python)
│   └── web/          # Next.js 前端 (TypeScript/React)
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
    ROLE_NOT_FOUND = "ROLE_NOT_FOUND"            # 新增
    ROLE_ALREADY_EXISTS = "ROLE_ALREADY_EXISTS"
    ROLE_BUILTIN_PROTECTED = "ROLE_BUILTIN_PROTECTED"

ERROR_STATUS_MAP[ErrorCode.ROLE_NOT_FOUND] = status.HTTP_404_NOT_FOUND

def raise_role_not_found(detail=None) -> NoReturn:
    raise BusinessException(code=ErrorCode.ROLE_NOT_FOUND, detail=detail)
```

### Scope 权限体系

统一在 [`app/core/scopes.py`](apps/api/app/core/scopes.py) 中扩展：

```python
class RoleScope(str, Enum):
    READ = "role:read"
    CREATE = "role:create"
    UPDATE = "role:update"
    DELETE = "role:delete"

ALL_ROLE_SCOPES = [RoleScope.READ, RoleScope.CREATE, RoleScope.UPDATE, RoleScope.DELETE]
ALL_SCOPES = ALL_USER_SCOPES + ALL_ROLE_SCOPES   # 记得加入总集合！
```

路由中使用三个依赖函数（定义在 [`app/core/dependencies.py`](apps/api/app/core/dependencies.py)）：

```python
from app.core.dependencies import require_scope, require_any_scope, require_all_scopes

@router.get("/", response_model=RolesPublic)
async def read_roles(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Query()],
    _: Annotated[None, Depends(require_scope(RoleScope.READ))],
) -> Any: ...

@router.delete("/{role_id}")
async def delete_role(
    session: SessionDep,
    role_id: uuid.UUID,
    _: Annotated[None, Depends(require_any_scope(RoleScope.ADMIN, RoleScope.DELETE))],
) -> Message: ...
```

> **超管天然拥有全部 scope**（`is_superuser=True`），无需特判。预置角色（viewer/editor/admin）在 `init_roles_and_scopes()` 启动时初始化，不可修改/删除。

---

## ➕ 新增一个业务域的完整流程

> 以下按步骤接入新业务域。示例用 `<name>` 占位（如 `order` / `post` / `product`），对应类名用 `Xxx` / `<Name>Scope`（如 `Order` / `OrderScope`）。可对照已落地的 `user` / `role` 两个域（[`domains/user/`](apps/api/app/domains/user/) 与 [`domains/role/`](apps/api/app/domains/role/)）。

### 第 1 步：定义数据库模型

在 [`apps/api/app/core/models.py`](apps/api/app/core/models.py) 添加模型：

```python
class Xxx(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=50)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc, sa_type=DateTime(timezone=True)
    )
```

### 第 2 步：生成数据库迁移

```bash
cd apps/api
uv run alembic revision --autogenerate -m "add <name> table"
uv run alembic upgrade head
```

### 第 3 步：创建 Domain 模块（6 个文件）

复制 `domains/role/` 的骨架，逐文件改造：

| 文件 | 核心内容 |
|------|----------|
| `schemas.py` | `XxxCreate` / `XxxUpdate` / `XxxPublic` / `XxxsPublic(PaginatedResponse[XxxPublic])` |
| `repository.py` | `get_xxx` / `get_xxx_list`（分页+count）/ `create_xxx`（flush）/ `update_xxx` / `delete_xxx` |
| `service.py` | 唯一性预检 → repository → `commit`；`IntegrityError` 兜底 |
| `responses.py` | `xxx_public` / `xxxs_public`（批量 scope 查询） |
| `router.py` | RESTful 路由 + `require_scope(<Name>Scope.X)` |
| `__init__.py` | 空文件 |

> ⚠️ SQLModel `Relationship` 字段类型必须用 `Optional["Xxx"]` 写法，**不能用 `"Xxx | None"`**（SQLAlchemy 无法解析 union 语法字符串注解）。

### 第 4 步：注册 Scope（两个文件）

- [`app/core/scopes.py`](apps/api/app/core/scopes.py)：新增 `<Name>Scope` 枚举 + `ALL_<NAME>_SCOPES` + 加入 `ALL_SCOPES`
- [`packages/contracts/src/scopes.ts`](packages/contracts/src/scopes.ts)：同步新增 `<Name>Scope` 常量 + `ALL_<NAME>_SCOPES` + 更新 `ScopeType` 联合类型 + `ALL_SCOPES` + `DEFAULT_ROLE_SCOPES`

> ⚠️ **前后端必须保持 scope 字符串一致**，这是契约同步的硬约束。

### 第 5 步：注册路由

在 [`apps/api/app/api/v1/api.py`](apps/api/app/api/v1/api.py) 添加：

```python
from app.domains.xxx.router import router as xxx_router

router.include_router(xxx_router, prefix="/<name>s", tags=["<name>s"])
```

### 第 6 步：生成 SDK

```bash
cd packages/sdk
pnpm generate     # 从仓库内 openapi.json 快照离线生成客户端 + React Query Hooks
```

> **SDK 生成策略**：`packages/sdk/openapi.json` 是后端 OpenAPI 的**提交到仓库的快照**，`generate` 从该文件离线生成——因此 CI / 新接入方无需启动后端即可构建。
> 后端接口变更后刷新快照：
> ```bash
> # 启动后端后：
> cd packages/sdk && pnpm generate:live   # 拉取 http://localhost:8000/openapi.json 覆盖快照 + 重新生成
> ```

### 第 7 步：编写测试

在 [`apps/api/tests/`](apps/api/tests/) 新建 `test_<name>s.py`，复用现有测试夹具（`db_session` / `client` / `authorized_client` / `superuser_client`）：

```python
@pytest.mark.asyncio
async def test_create_xxx_success(superuser_client: AsyncClient):
    response = await superuser_client.post(
        "/v1/<name>s/", json={"name": "XXX-1"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "XXX-1"
```

运行测试：

```bash
cd apps/api && pytest    # 或 pnpm test
```

### 第 8 步：前端开发（可选）

按 [`apps/web/features/user/`](apps/web/features/user/)（或 `features/role/`）模板创建 `features/<name>/`：

```
features/<name>/
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
├── server/                 # 服务端组件（List / Detail）
└── stores/                 # （可选）全局状态（如 auth store，纯 CRUD 域可省略）
```

在 [`apps/web/components/sidebar.tsx`](apps/web/components/sidebar.tsx) 添加导航项到 `navigation` 或 `adminNavigation` 数组，并按 scope 过滤可见性（本模板实际做法见 `sidebar.tsx` 的 `visibleAdmin` 过滤逻辑）：

```tsx
import { <Name>Scope, hasScope } from '@repo/contracts/scopes';
import { YourIcon } from "lucide-react";

const adminNavigation = [
  // ...现有项
  { name: "<Name>管理", href: "/dashboard/<name>s", icon: YourIcon },
];

// 在 Sidebar 组件中按 scope 过滤：
const visibleAdmin = adminNavigation.filter((item) => {
  if (item.href === "/dashboard/<name>s") return hasScope(userScopes, <Name>Scope.READ);
  // ...
  return true;
});
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

- **scope 命名**：统一 `资源:操作` 格式（`user:read`、`role:admin`）
- **超管**：`is_superuser=True` 自动拥有全部 scope（`get_user_scopes()` 实现，见 [`dependencies.py`](apps/api/app/core/dependencies.py)）
- **角色**：用户经角色获得 scope；预置角色在 `init_roles_and_scopes()` 启动时初始化（[`database.py`](apps/api/app/core/database.py)）
- **预置角色不可修改/删除**：`BUILTIN_ROLES = ("viewer", "editor", "admin")`

### 三种权限检查粒度

| 函数 | 语义 | 示例 |
|------|------|------|
| `require_scope` | 必须拥有该 scope | `require_scope(UserScope.READ)` |
| `require_any_scope` | 满足任意一个即可 | `require_any_scope(UserScope.ADMIN, UserScope.DELETE)`（用户删除的真实用法） |
| `require_all_scopes` | 必须全部拥有 | `require_all_scopes(UserScope.READ, RoleScope.READ)` |

---

## 🔄 前后端契约同步

新增错误码 / Scope / 分页改动时，**必须同步**以下文件：

| 后端 | 前端契约包 |
|------|-----------|
| [`apps/api/app/core/errors.py`](apps/api/app/core/errors.py) | [`packages/contracts/src/errors.ts`](packages/contracts/src/errors.ts) |
| [`apps/api/app/core/scopes.py`](apps/api/app/core/scopes.py) | [`packages/contracts/src/scopes.ts`](packages/contracts/src/scopes.ts) |
| [`apps/api/app/core/schemas.py`](apps/api/app/core/schemas.py)（分页协议） | [`packages/contracts/src/pagination.ts`](packages/contracts/src/pagination.ts) |

> ⚠️ 后端 `scopes.py` 与前端 `scopes.ts` 是**单一事实源的两个镜像**，字符串必须逐字一致。
> 验证方法：
> - 后端行为：`cd apps/api && pnpm test`
> - 契约一致性（自动比对 Python↔TS 镜像）：`cd packages/contracts && pnpm test`（`consistency.test.ts` 守护 8 项断言，任一侧改漏即红）

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
pnpm generate         # 从仓库内 openapi.json 快照重新生成 SDK（离线可用）
pnpm generate:live    # 启动后端后：拉取最新 OpenAPI 覆盖快照并重新生成
```

### CI（GitHub Actions）

`.github/workflows/ci.yml` 提供模板级 CI，push / PR 自动运行：

| Job | 内容 |
|-----|------|
| **Backend** | `uv sync` → `ruff check` → `pytest`（59+ 用例） |
| **Frontend** | `pnpm install` → 离线生成 SDK → `check-types` → `lint` → `test`（web + contracts vitest） |

无需启动后端：SDK 从仓库内 `openapi.json` 快照离线生成，契约一致性由 `consistency.test.ts` 守护。

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
| [`apps/web/components/`](apps/web/components/) | 全局 UI 组件（sidebar、brand、theme-toggle、providers、shadcn/ui） |
| [`apps/web/features/`](apps/web/features/) | 前端业务模块——**新前端业务参考范例** |
| [`apps/web/lib/`](apps/web/lib/) | 工具函数（API SDK 客户端、utils） |
| [`packages/contracts/src/`](packages/contracts/src/) | 共享契约（错误码、Scope、分页、常量） |
| [`packages/sdk/src/`](packages/sdk/src/) | OpenAPI 自动生成 SDK（生成物，禁止手改） |
| [`packages/sdk/openapi.json`](packages/sdk/openapi.json) | 后端 OpenAPI 快照（`pnpm generate` 的输入，接口变更后跑 `generate:live` 刷新） |
| [`packages/ui/src/`](packages/ui/src/) | 共享 UI 组件 |
| [`.github/workflows/`](.github/workflows/) | CI（push / PR 自动跑 backend + frontend 全部检查） |
