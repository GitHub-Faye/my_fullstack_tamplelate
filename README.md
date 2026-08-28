# My Fullstack Template

全栈开发模板，基于 **FastAPI + Next.js + SQLite + TanStack Query** 的现代化 Monorepo 架构。

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
| **前端** | Next.js 16 + React 19 + TanStack Query + shadcn/ui | [`apps/web/`](apps/web/) |
| **SDK** | OpenAPI 自动生成客户端 + React Query Hooks | [`packages/sdk/`](packages/sdk/sdk.md) |
| **契约** | 共享错误码/Scope/分页协议 | [`packages/contracts/`](packages/contracts/contracts.md) |
| **UI** | 共享 React 组件 | [`packages/ui/`](packages/ui/) |
| **文档** | Next.js 文档站 | [`apps/docs/`](apps/docs/) |

**数据流：** `前端 (Next.js)` → `SDK (@repo/sdk)` → `API (FastAPI)` → `SQLite`

---

## 🚀 首次启动（5 步）

### 1. 安装依赖

```bash
# 安装 Node 依赖（根目录）
pnpm install

# 安装 Python 依赖
uv venv --python 3.11.15 
uv sync 
```

### 2. 准备数据库

本项目默认使用 **SQLite**（文件数据库），无需 Docker 或外部数据库服务。
启动时如数据库文件不存在会自动创建（迁移见第 3 步）。

> 如需使用 MySQL / PostgreSQL，在 [`apps/api/.env`](apps/api/.env) 中设置 `DATABASE_URL` 即可，例如：
> `DATABASE_URL=mysql+asyncmy://user:pass@host:3306/dbname`
> `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname`

### 3. 数据库迁移

```bash
cd apps/api
uv run alembic upgrade head
```

迁移配置在 [`migrations/env.py`](apps/api/migrations/env.py)，模型定义在 [`app/core/models.py`](apps/api/app/core/database.py)。

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

## 🔧 开发新功能的完整流程

以新增一个 **"分类（Category）"** 功能为例，演示完整的 **后端 → SDK → 前端** 链路。

```
修改 Model → alembic 迁移 → 写 Domain 路由/Repository
       ↓
  SDK 重新生成 (pnpm generate)
       ↓
  写前端 Feature (queries → 组件 → 页面)
       ↓
  如有新错误码/Scope → 同步 contracts 包
```

---

### 🟢 阶段 1：后端开发（Domain 驱动）

#### 1.1 创建数据库模型

在 [`apps/api/app/core/models.py`](apps/api/app/core/database.py) 添加模型：

```python
class Category(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    description: str | None = Field(default=None, max_length=500)
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)
```

#### 1.2 生成迁移文件

```bash
cd apps/api
alembic revision --autogenerate -m "add category table"
alembic upgrade head
```

#### 1.3 创建 Domain 模块

按 [`apps/api/app/domains/item/`](apps/api/app/domains/item/) 的模板，创建 `domains/category/` 目录，包含四个文件：

| 文件 | 职责 | 参考模版 |
|------|------|----------|
| [`schemas.py`](apps/api/app/domains/item/schemas.py) | Pydantic 请求/响应 Schema | 定义 `CategoryCreate`、`CategoryPublic`、`CategoryUpdate` |
| [`repository.py`](apps/api/app/domains/item/repository.py) | 数据库 CRUD 操作 | SQLModel 异步查询 |
| [`dependencies.py`](apps/api/app/domains/item/dependencies.py) | 依赖注入（权限检查） | 所有权校验 |
| [`router.py`](apps/api/app/domains/item/router.py) | API 路由定义 | RESTful 路由 + Scope 装饰器 |

#### 1.4 注册路由

在 [`apps/api/app/api/v1/api.py`](apps/api/app/api/v1/api.py) 添加：

```python
from app.domains.category.router import router as category_router

router.include_router(category_router, prefix="/categories", tags=["categories"])
```

---

### 🟡 阶段 2：SDK 自动生成

后端 API 写好后，运行 OpenAPI 生成命令：

```bash
cd packages/sdk
pnpm generate     # 执行 openapi-ts.config.ts
```

这会自动更新 [`packages/sdk/src/api/`](packages/sdk/src/api/) 目录下的所有文件：

| 文件 | 用途 |
|------|------|
| `sdk.gen.ts` | API 客户端方法 |
| `types.gen.ts` | TypeScript 类型 |
| `zod.gen.ts` | Zod 校验 Schema |
| `@tanstack/react-query.gen.ts` | TanStack Query Hooks（`useQuery` / `useMutation`） |

---

### 🟠 阶段 3：更新业务契约

如果新增了错误码或 Scope，同步更新 [`packages/contracts/`](packages/contracts/contracts.md)：

| 后端文件 | 前端对应文件 |
|----------|-------------|
| [`app/core/errors.py`](apps/api/app/core/errors.py) | [`packages/contracts/src/errors.ts`](packages/contracts/src/errors.ts) |
| [`app/core/scopes.py`](apps/api/app/core/scopes.py) | [`packages/contracts/src/scopes.ts`](packages/contracts/src/scopes.ts) |
| [`app/core/schemas.py`](apps/api/app/core/schemas.py)（分页） | [`packages/contracts/src/pagination.ts`](packages/contracts/src/pagination.ts) |

---

### 🔵 阶段 4：前端开发

#### 4.1 创建 Feature 模块

按 [`apps/web/features/item/`](apps/web/features/item/) 模板，创建 `features/category/`：

```
features/category/
├── index.ts                # 统一导出
├── api/
│   ├── index.ts
│   ├── client/             # 客户端组件数据获取
│   │   ├── index.ts
│   │   └── queries.ts      # TanStack Query Hooks
│   └── server/             # 服务端组件数据获取
│       ├── index.ts
│       └── queries.ts
├── client/                 # 客户端组件
│   ├── index.ts
│   ├── CategoryTable.tsx    # 列表表格
│   ├── CategoryForm.tsx     # 新增/编辑表单
│   └── CategoryDetail.tsx   # 详情
├── schemas/
│   └── category.ts          # 前端业务类型（如需额外定义）
└── server/                 # 服务端组件
    ├── index.ts
    ├── CategoryList.tsx
    └── CategoryDetail.tsx
```

#### 4.2 创建页面路由

在 `apps/web/app/(dashboard)/dashboard/categories/` 下创建页面：

| 路由 | 注意事项 |
|------|----------|
| `page.tsx` | 列表页，参考 [`items/page.tsx`](apps/web/app/(dashboard)/dashboard/items/page.tsx) |
| `new/page.tsx` | 新建页 |
| `[id]/page.tsx` | 详情页 |
| `[id]/edit/page.tsx` | 编辑页 |

#### 4.3 SDK 使用方式

**客户端组件（带缓存、状态管理）：**

```tsx
// features/category/api/client/queries.ts
import { client } from '@/lib/api-sdk';
import {
  getCategoriesV1CategoriesGetQueryKey,
  readCategoriesV1CategoriesGet,
} from '@repo/sdk';

export function useCategories() {
  return useQuery({
    queryKey: getCategoriesV1CategoriesGetQueryKey(),
    queryFn: () => readCategoriesV1CategoriesGet({ client }),
  });
}
```

**服务端组件（直接调用）：**

```tsx
// features/category/api/server/queries.ts
import { createClient } from '@repo/sdk';
import { readCategoriesV1CategoriesGet } from '@repo/sdk';

export async function getCategories(accessToken: string) {
  const client = createClient({ headers: { Authorization: `Bearer ${accessToken}` } });
  return readCategoriesV1CategoriesGet({ client });
}
```

#### 4.4 添加导航

在 [`components/navbar.tsx`](apps/web/components/navbar.tsx) 中添加菜单项。

---

## 📐 架构约定

### 后端约定

| 约定 | 说明 |
|------|------|
| **Domain 划分** | 每个业务模块一个目录：`domains/<name>/` |
| **路由注册** | 统一在 [`app/api/v1/api.py`](apps/api/app/api/v1/api.py) 注册 |
| **权限控制** | 使用 `require_scope` / `require_any_scope` 装饰器 |
| **错误处理** | 使用 [`app/core/errors.py`](apps/api/app/core/errors.py) 中的统一错误函数 |
| **异步优先** | 所有数据库操作使用 SQLModel 异步接口 |
| **自动迁移** | 模型修改后运行 `alembic revision --autogenerate` |
| **定时/后台任务** | 暂未接入（Celery/RabbitMQ 已移除），后续需要可重新引入 |

### 前端约定

| 约定 | 说明 |
|------|------|
| **Feature 划分** | 每个业务模块一个目录：`features/<name>/` |
| **客户端/服务端** | 明确区分 `client/` 和 `server/` 子目录 |
| **API 调用** | 客户端通过 TanStack Query + SDK，服务端通过 SDK 直调 |
| **UI 组件** | 优先使用 [`components/ui/`](apps/web/components/ui/) 中的 shadcn/ui 组件 |
| **表单** | 使用 `react-hook-form` + `zod` 校验 |
| **主题** | 使用 `next-themes` 暗色模式 |
| **Auth** | JWT Token 存储在 Cookie 中，[`middleware.ts`](apps/web/middleware.ts) 处理路由保护 |

---

## 🔐 自定义角色和权限管理

本项目已内置完善的 **RBAC（Role-Based Access Control）** 系统。下面从 4 个维度讲解如何自定义。

### 权限系统架构

```
User ────┐
User ────┼─── (多对多) ──── Role ──── (一对多) ──── Scope
User ────┘                    │                     │
                              │                     ├─ item:read
                              │                     ├─ item:create
                              │                     ├─ item:admin
                              │                     └─ ...
                              │
                              ├─ viewer  → [item:read]
                              ├─ editor  → [item:read, create, ...]
                              └─ admin   → [全部 item 权限]
```

**核心数据表**（定义在 [`app/core/models.py`](apps/api/app/core/models.py)）：

| 表 | 用途 |
|----|------|
| `Role` | 角色定义（如 viewer, editor, admin） |
| `RoleScope` | 角色与权限的关联（一个角色有多个 scope） |
| `UserRole` | 用户与角色的多对多关联 |

### 后端自定义步骤（以 "订单 Order" 为例）

#### 步骤 1：在 [`app/core/scopes.py`](apps/api/app/core/scopes.py) 定义 Scope

```python
from enum import Enum

class OrderScope(str, Enum):
    """Order 资源的权限范围"""
    READ = "order:read"
    CREATE = "order:create"
    UPDATE = "order:update"
    DELETE = "order:delete"
    ADMIN = "order:admin"

ALL_ORDER_SCOPES = [
    OrderScope.READ,
    OrderScope.CREATE,
    OrderScope.UPDATE,
    OrderScope.DELETE,
    OrderScope.ADMIN,
]
```

#### 步骤 2：在角色中分配新 Scope

在同一个文件 [`scopes.py`](apps/api/app/core/scopes.py) 的 `DEFAULT_ROLE_SCOPES` 中添加：

```python
DEFAULT_ROLE_SCOPES = {
    "viewer": [
        ItemScope.READ,
        OrderScope.READ,            # ← 新增
    ],
    "editor": [
        ItemScope.READ,
        ItemScope.CREATE,
        ItemScope.UPDATE,
        ItemScope.DELETE,
        OrderScope.READ,
        OrderScope.CREATE,          # ← 新增
        OrderScope.UPDATE,          # ← 新增
    ],
    "admin": [
        ItemScope.READ,
        ItemScope.CREATE,
        ItemScope.UPDATE,
        ItemScope.DELETE,
        ItemScope.ADMIN,
        OrderScope.READ,
        OrderScope.CREATE,
        OrderScope.UPDATE,
        OrderScope.DELETE,
        OrderScope.ADMIN,           # ← 新增
    ],
}
```

角色初始化逻辑在 [`app/core/database.py`](apps/api/app/core/database.py) 的 `init_roles_and_scopes()` 中自动完成——启动应用时会自动创建默认角色并分配 scope。

#### 步骤 3：在路由中使用 Scope

在路由中通过 `require_scope`、`require_any_scope`、`require_all_scopes` 三个依赖函数做权限检查（定义在 [`app/core/dependencies.py`](apps/api/app/core/dependencies.py)）：

```python
from app.core.scopes import OrderScope
from app.core.dependencies import require_scope, require_any_scope

@router.get("/", response_model=OrdersPublic)
async def read_orders(
    session: SessionDep,
    current_user: CurrentUser,
    pagination: Annotated[PaginationParams, Query()],
    _: Annotated[None, Depends(require_scope(OrderScope.READ))],  # ← 需要 order:read
) -> Any:
    ...

@router.post("/", response_model=OrderPublic)
async def create_order(
    session: SessionDep,
    current_user: CurrentUser,
    order_in: OrderCreate,
    _: Annotated[None, Depends(require_scope(OrderScope.CREATE))],  # ← 需要 order:create
) -> Any:
    ...

@router.put("/{order_id}", response_model=OrderPublic)
async def update_order(
    session: SessionDep,
    current_user: CurrentUser,
    order_id: uuid.UUID,
    order_in: OrderUpdate,
    _: Annotated[None, Depends(require_any_scope(OrderScope.UPDATE, OrderScope.ADMIN))],  # ← 二选一
) -> Any:
    ...

@router.delete("/{order_id}")
async def delete_order(
    session: SessionDep,
    current_user: CurrentUser,
    order_id: uuid.UUID,
    _: Annotated[None, Depends(require_all_scopes(OrderScope.DELETE))],  # ← 必需
) -> Message:
    ...
```

#### 步骤 4：自定义新角色

如果需要添加完全新的角色（如 `auditor` 审计员），在 `DEFAULT_ROLE_SCOPES` 中新增即可：

```python
DEFAULT_ROLE_SCOPES = {
    # ... 已有角色省略
    
    "auditor": [                    # ← 新增角色
        ItemScope.READ,
        OrderScope.READ,
        UserScope.READ,
        SystemScope.READ,
    ],
}
```

应用启动时 `init_roles_and_scopes()` 会自动创建该角色。

> **注意**：`is_superuser` 用户拥有所有权限（参见 [`dependencies.py`](apps/api/app/core/dependencies.py#L168-L181) 的 `get_user_scopes()`），不受角色 scope 限制。

### 前端同步步骤

#### 步骤 1：更新 [`packages/contracts/src/scopes.ts`](packages/contracts/src/scopes.ts)

```typescript
/** Order 资源的权限 Scope */
export const OrderScope = {
  READ: "order:read",
  CREATE: "order:create",
  UPDATE: "order:update",
  DELETE: "order:delete",
  ADMIN: "order:admin",
} as const;

export type OrderScopeType = typeof OrderScope[keyof typeof OrderScope];

export const ALL_ORDER_SCOPES: OrderScopeType[] = [
  OrderScope.READ,
  OrderScope.CREATE,
  OrderScope.UPDATE,
  OrderScope.DELETE,
  OrderScope.ADMIN,
];
```

#### 步骤 2：更新 Scope 联合类型

```typescript
export type ScopeType = ItemScopeType | UserScopeType | SystemScopeType | OrderScopeType;

export const ALL_SCOPES: ScopeType[] = [
  ...ALL_ITEM_SCOPES,
  ...ALL_USER_SCOPES,
  ...Object.values(SystemScope),
  ...ALL_ORDER_SCOPES,         // ← 新增
];
```

#### 步骤 3：更新默认角色

```typescript
export const DEFAULT_ROLE_SCOPES: Record<string, ScopeType[]> = {
  viewer: [ItemScope.READ, UserScope.READ, OrderScope.READ],
  editor: [
    ItemScope.READ, ItemScope.CREATE, ItemScope.UPDATE, ItemScope.DELETE,
    UserScope.READ,
    OrderScope.READ, OrderScope.CREATE, OrderScope.UPDATE,
  ],
  admin: [
    ItemScope.READ, ItemScope.CREATE, ItemScope.UPDATE, ItemScope.DELETE, ItemScope.ADMIN,
    UserScope.READ, UserScope.CREATE, UserScope.UPDATE, UserScope.DELETE, UserScope.ADMIN,
    SystemScope.READ,
    OrderScope.READ, OrderScope.CREATE, OrderScope.UPDATE, OrderScope.DELETE, OrderScope.ADMIN,
  ],
  auditor: [ItemScope.READ, OrderScope.READ, UserScope.READ, SystemScope.READ],  // ← 新角色
  superuser: [...ALL_SCOPES],
};
```

#### 步骤 4：前端 UI 中检查权限

```tsx
import { OrderScope, hasScope, hasAnyScope } from '@repo/contracts/scopes';

function OrderList() {
  const { data: user } = useCurrentUser();
  const userScopes = user?.scopes ?? [];

  // 检查单权限
  if (!hasScope(userScopes, OrderScope.READ)) {
    return <div>无权限查看订单</div>;
  }

  // 检查多权限（或）
  const canWrite = hasAnyScope(userScopes, [OrderScope.CREATE, OrderScope.ADMIN]);
  
  return (
    <div>
      <OrderTable />
      {canWrite && <Button>新建订单</Button>}
    </div>
  );
}
```

### 权限自定义完整流程图

```
                   后端 (Python)                             前端 (TypeScript)
          ┌──────────────────────┐                ┌──────────────────────┐
  Step 1  │ scopes.py 定义 Enum  │                │ scopes.ts 定义常量   │
          │ OrderScope.READ =    │   同步 ────→   │ OrderScope.READ =    │
          │   "order:read"       │                │   "order:read"       │
          └────────┬─────────────┘                └────────┬─────────────┘
                   │                                       │
  Step 2  ┌────────▼─────────────┐                ┌────────▼─────────────┐
          │ DEFAULT_ROLE_SCOPES  │   同步 ────→   │ DEFAULT_ROLE_SCOPES  │
          │ 给角色分配 scope      │                │ 给角色分配 scope      │
          └────────┬─────────────┘                └────────┬─────────────┘
                   │                                       │
  Step 3  ┌────────▼─────────────┐                ┌────────▼─────────────┐
          │ dependencies.py      │                │ hasScope() 检查权限  │
          │ require_scope() 装饰  │                │ 前端 UI 条件渲染     │
          │ Router 中应用         │                │                      │
          └────────┬─────────────┘                └──────────────────────┘
                   │
          ┌────────▼─────────────┐
          │ database.py          │
          │ init_roles_and_scopes│
          │ 启动时自动初始化角色   │
          └──────────────────────┘
```

### 注意事项

| 注意点 | 说明 |
|--------|------|
| **前后端同步** | [`scopes.py`](apps/api/app/core/scopes.py) 和 [`scopes.ts`](packages/contracts/src/scopes.ts) 必须保持一致的 scope 字符串 |
| **角色初始化** | [`database.py`](apps/api/app/core/database.py) 的 `init_roles_and_scopes()` 只在角色不存在时创建，不会覆盖已有角色 |
| **超管绕过** | `is_superuser=true` 的用户自动拥有所有 scope，不过滤（参见 [`dependencies.py`](apps/api/app/core/dependencies.py#L168-L181)） |
| **Scope 命名** | 统一采用 `资源:操作` 格式，如 `order:read`、`order:admin` |
| **依赖函数** | `require_scope`（必需）、`require_any_scope`（任一）、`require_all_scopes`（全部）三种粒度 |

---

## 📊 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    apps/web (Next.js)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ features/item│  │features/user│  │features/cat..│   │
│  │ client/server│  │ client/server│  │ client/server│   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │           │
│    ┌────▼─────────────────▼─────────────────▼────┐      │
│    │           @repo/sdk (TanStack Query)         │      │
│    └────────────────────┬────────────────────────┘      │
└─────────────────────────┼──────────────────────────────┘
                          │ HTTP
┌─────────────────────────▼──────────────────────────────┐
│              apps/api (FastAPI + Domain)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ domains/item │  │ domains/user │  │domains/cat.. │  │
│  │router/repo/  │  │router/repo/  │  │router/repo/  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         └────────┬────────┘────────┬────────┘          │
│                  ▼                 ▼                    │
│                ┌──────┐                                 │
│                │SQLite│                                 │
│                └──────┘                                 │
└─────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────┐
│                    apps/web (Next.js)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ features/item│  │features/user│  │features/cat..│   │
│  │ client/server│  │ client/server│  │ client/server│   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │           │
│    ┌────▼─────────────────▼─────────────────▼────┐      │
│    │           @repo/sdk (TanStack Query)         │      │
│    └────────────────────┬────────────────────────┘      │
└─────────────────────────┼──────────────────────────────┘
                          │ HTTP
┌─────────────────────────▼──────────────────────────────┐
│              apps/api (FastAPI + Domain)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ domains/item │  │ domains/user │  │domains/cat.. │  │
│  │router/repo/  │  │router/repo/  │  │router/repo/  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         └────────┬────────┘────────┬────────┘          │
│                  ▼                 ▼                    │
│                ┌──────┐                                 │
│                │SQLite│                                 │
│                └──────┘                                 │
└─────────────────────────────────────────────────────────┘
```

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
alembic upgrade head  # 数据库迁移
alembic revision --autogenerate -m "描述"  # 生成迁移

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
| [`apps/api/app/core/`](apps/api/app/core/) | 后端核心（配置、数据库、安全、中间件、日志） |
| [`apps/api/app/domains/`](apps/api/app/domains/) | 业务模块（item、user） |
| [`apps/api/app/api/v1/`](apps/api/app/api/v1/) | API 路由注册入口 |
| [`apps/api/migrations/`](apps/api/migrations/) | Alembic 数据库迁移 |
| [`apps/api/tests/`](apps/api/tests/) | 后端测试 |
| [`apps/web/app/`](apps/web/app/) | Next.js 页面路由 |
| [`apps/web/components/`](apps/web/components/) | 全局 UI 组件（navbar、providers、shadcn/ui） |
| [`apps/web/features/`](apps/web/features/) | 前端业务模块 |
| [`apps/web/lib/`](apps/web/lib/) | 工具函数（API SDK 客户端、utils） |
| [`packages/contracts/src/`](packages/contracts/src/) | 共享契约（错误码、Scope、分页、常量） |
| [`packages/sdk/src/`](packages/sdk/src/) | OpenAPI 自动生成 SDK |
| [`packages/ui/src/`](packages/ui/src/) | 共享 UI 组件 |