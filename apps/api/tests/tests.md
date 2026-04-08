# 测试文档

本文档记录 `apps/api` 项目的测试架构、测试用例和运行指南。

## 测试架构

### 技术栈

- **pytest**: Python 测试框架
- **pytest-asyncio**: 异步测试支持
- **httpx**: 异步 HTTP 客户端 (AsyncClient)
- **FastAPI Dependency Overrides**: 依赖注入覆盖
- **pytest-cov**: 代码覆盖率报告
- **aiosqlite**: 异步 SQLite 内存数据库

### 测试目录结构

```
apps/api/tests/
├── __init__.py          # 测试包初始化
├── conftest.py          # pytest fixtures 配置
├── utils.py             # 测试工具函数
├── test_login.py        # 登录认证测试 (9个测试)
├── test_users.py        # 用户管理测试 (25个测试)
├── test_items.py        # 物品管理测试 (21个测试)
└── tests.md             # 本文档
```

## 核心 Fixtures

### 数据库 Fixtures

| Fixture | 作用 | Scope |
|---------|------|-------|
| `engine` | 创建异步数据库引擎 | function |
| `db_session` | 提供数据库会话，自动创建/删除表 | function |

### 应用 Fixtures

| Fixture | 作用 | Scope |
|---------|------|-------|
| `app` | 配置好的 FastAPI 应用，覆盖数据库依赖 | function |
| `client` | 未授权的 HTTP 客户端 | function |
| `authorized_client` | 已授权的普通用户客户端 | function |
| `superuser_client` | 已授权的超级管理员客户端 | function |

### 数据 Fixtures

| Fixture | 作用 |
|---------|------|
| `test_user` | 普通测试用户 |
| `test_superuser` | 超级管理员测试用户 |
| `test_item` | 测试物品（属于 test_user） |
| `user_token` | 普通用户的 JWT 令牌 |
| `superuser_token` | 超级管理员的 JWT 令牌 |

## 测试用例详情

### test_login.py - 登录认证测试 (9个)

| 测试名称 | 描述 |
|----------|------|
| `test_login_access_token_success` | 使用正确的邮箱和密码登录成功 |
| `test_login_access_token_wrong_password` | 使用错误的密码登录失败 |
| `test_login_access_token_nonexistent_user` | 使用不存在的用户登录失败 |
| `test_login_access_token_inactive_user` | 使用未激活的用户登录失败 |
| `test_test_token_valid` | 使用有效的 token 获取当前用户信息 |
| `test_test_token_no_token` | 没有提供 token 时访问受保护端点失败 |
| `test_test_token_invalid_token` | 使用无效的 token 访问受保护端点失败 |
| `test_reset_password_invalid_token` | 使用无效的令牌重置密码失败 |

### test_users.py - 用户管理测试 (25个)

#### 用户注册 (4个)
| 测试名称 | 描述 |
|----------|------|
| `test_register_user_success` | 用户自助注册成功 |
| `test_register_user_duplicate_email` | 使用已存在的邮箱注册失败 |
| `test_register_user_invalid_email` | 使用无效的邮箱格式注册失败 |
| `test_register_user_short_password` | 使用太短的密码注册失败 |

#### 当前用户操作 (7个)
| 测试名称 | 描述 |
|----------|------|
| `test_read_user_me` | 获取当前登录用户的信息 |
| `test_read_user_me_unauthorized` | 未登录用户无法获取用户信息 |
| `test_update_user_me` | 更新当前用户自己的信息 |
| `test_update_user_me_duplicate_email` | 更新邮箱为已被其他用户使用的邮箱失败 |
| `test_update_password_me_success` | 成功修改当前用户密码 |
| `test_update_password_me_wrong_current` | 使用错误的当前密码修改密码失败 |
| `test_update_password_me_same_password` | 新密码与当前密码相同时失败 |
| `test_delete_user_me_success` | 成功删除当前用户自己的账户 |
| `test_delete_user_me_superuser` | 超级管理员不能删除自己的账户 |

#### 超级管理员操作 (14个)
| 测试名称 | 描述 |
|----------|------|
| `test_read_users_superuser` | 超级管理员获取所有用户列表 |
| `test_read_users_normal_user` | 普通用户无法获取所有用户列表 |
| `test_create_user_superuser` | 超级管理员创建新用户 |
| `test_create_user_duplicate_email_superuser` | 超级管理员创建已存在邮箱的用户失败 |
| `test_read_user_by_id_own` | 用户获取自己的信息 |
| `test_read_user_by_id_other_normal_user` | 普通用户无法获取其他用户的信息 |
| `test_read_user_by_id_superuser` | 超级管理员可以获取任何用户的信息 |
| `test_update_user_superuser` | 超级管理员更新其他用户信息 |
| `test_update_user_not_found_superuser` | 超级管理员更新不存在的用户失败 |
| `test_delete_user_superuser` | 超级管理员删除其他用户 |
| `test_delete_user_self_superuser` | 超级管理员不能删除自己 |
| `test_delete_user_not_found_superuser` | 超级管理员删除不存在的用户失败 |

### test_items.py - 物品管理测试 (21个)

#### 获取物品列表 (4个)
| 测试名称 | 描述 |
|----------|------|
| `test_read_items_normal_user` | 普通用户获取自己的物品列表 |
| `test_read_items_pagination` | 物品列表分页功能 |
| `test_read_items_superuser_sees_all` | 超级管理员可以看到所有用户的物品 |
| `test_read_items_unauthorized` | 未登录用户无法获取物品列表 |

#### 获取单个物品 (5个)
| 测试名称 | 描述 |
|----------|------|
| `test_read_item_by_id_owner` | 物品所有者可以获取自己的物品 |
| `test_read_item_by_id_not_found` | 获取不存在的物品返回 404 |
| `test_read_item_by_id_other_user` | 普通用户无法获取其他用户的物品 |
| `test_read_item_by_id_superuser_can_access_any` | 超级管理员可以获取任何物品 |

#### 创建物品 (4个)
| 测试名称 | 描述 |
|----------|------|
| `test_create_item_success` | 成功创建物品 |
| `test_create_item_validation_error` | 创建物品时验证失败（缺少必填字段） |
| `test_create_item_empty_title` | 创建物品时标题为空失败 |
| `test_create_item_unauthorized` | 未登录用户无法创建物品 |

#### 更新物品 (5个)
| 测试名称 | 描述 |
|----------|------|
| `test_update_item_success` | 成功更新自己的物品 |
| `test_update_item_partial` | 部分更新物品（只更新描述） |
| `test_update_item_not_found` | 更新不存在的物品返回 404 |
| `test_update_item_other_user` | 普通用户无法更新其他用户的物品 |
| `test_update_item_superuser_can_update_any` | 超级管理员可以更新任何物品 |

#### 删除物品 (5个)
| 测试名称 | 描述 |
|----------|------|
| `test_delete_item_success` | 成功删除自己的物品 |
| `test_delete_item_not_found` | 删除不存在的物品返回 404 |
| `test_delete_item_other_user` | 普通用户无法删除其他用户的物品 |
| `test_delete_item_superuser_can_delete_any` | 超级管理员可以删除任何物品 |
| `test_delete_item_unauthorized` | 未登录用户无法删除物品 |

## 运行测试

### 基本命令

```bash
cd apps/api

# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_login.py -v

# 运行特定测试函数
python -m pytest tests/test_login.py::test_login_access_token_success -v
```

### 覆盖率报告

```bash
# 生成终端覆盖率报告
python -m pytest tests/ --cov=app --cov-report=term

# 生成 HTML 覆盖率报告
python -m pytest tests/ --cov=app --cov-report=html

# 生成详细覆盖率报告（显示未覆盖的行）
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### 调试模式

```bash
# 显示详细的错误信息
python -m pytest tests/ -v --tb=long

# 在第一个失败处停止
python -m pytest tests/ -v --maxfail=1

# 只运行失败的测试
python -m pytest tests/ --lf
```

## 测试设计原则

### 1. 完全隔离

每个测试函数都有独立的数据库会话和表结构，测试之间不会相互影响。

### 2. 无需外部服务

- 使用内存 SQLite 数据库，无需 PostgreSQL
- 使用 ASGITransport 直接调用 FastAPI，无需启动服务器
- 所有测试在 3-5 秒内完成

### 3. 依赖覆盖

通过 FastAPI 的 `dependency_overrides` 机制注入测试数据库会话：

```python
@app.dependency_overrides
def override_get_db():
    yield db_session
```

### 4. 认证测试

使用 JWT 令牌进行认证测试：

```python
async with AsyncClient(transport=transport, base_url="http://test") as ac:
    ac.headers["Authorization"] = f"Bearer {token}"
    yield ac
```

## 已知限制

### SQLite UUID 处理

SQLite 对 UUID 类型的支持有限，某些测试可能会遇到类型转换问题。在生产环境使用 PostgreSQL 时，这些问题不会出现。

### OAuth2 状态码

未授权请求可能返回 401 或 403，取决于 FastAPI 的 OAuth2 实现。测试中接受两种状态码。

## 扩展测试

### 添加新测试

1. 在相应的测试文件中添加测试函数
2. 使用 `@pytest.mark.asyncio` 装饰器
3. 使用提供的 fixtures 获取测试数据

示例：

```python
@pytest.mark.asyncio
async def test_new_feature(authorized_client: AsyncClient, test_user: User):
    response = await authorized_client.get("/v1/new-endpoint")
    assert response.status_code == 200
```

### 添加新 Fixture

在 `conftest.py` 中添加新的 fixture：

```python
@pytest_asyncio.fixture(scope="function")
async def new_fixture(db_session: AsyncSession) -> SomeModel:
    # 创建测试数据
    obj = SomeModel(...)
    db_session.add(obj)
    await db_session.commit()
    return obj
```

## 测试结果

- **总测试数**: 55 个
- **通过**: 55 个
- **失败**: 0 个
- **跳过**: 0 个

所有测试无需启动服务器或数据库即可运行。
