"""
Tests for item management endpoints.

Tests cover:
- Item CRUD operations
- Permission checks (owner/superuser)
- Pagination
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User, Item


# ======================== 获取物品列表测试 ========================

@pytest.mark.asyncio
async def test_read_items_normal_user(
    authorized_client: AsyncClient,
    test_user: User,
    test_item: Item
):
    """
    测试普通用户获取自己的物品列表。
    """
    response = await authorized_client.get("/v1/items/")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] == 1
    assert len(data["data"]) == 1
    assert data["data"][0]["title"] == test_item.title


@pytest.mark.asyncio
async def test_read_items_pagination(
    authorized_client: AsyncClient,
    test_user: User,
    db_session: AsyncSession
):
    """
    测试物品列表分页功能。
    """
    # 创建多个物品
    for i in range(5):
        item = Item(
            title=f"Item {i}",
            description=f"Description {i}",
            owner_id=test_user.id,
        )
        db_session.add(item)
    await db_session.commit()
    
    # 测试分页
    response = await authorized_client.get("/v1/items/?skip=0&limit=3")
    
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 5  # 5 new items created in this test
    assert len(data["data"]) == 3


@pytest.mark.asyncio
async def test_read_items_superuser_sees_all(
    superuser_client: AsyncClient,
    test_user: User,
    test_superuser: User,
    db_session: AsyncSession
):
    """
    测试超级管理员可以看到所有用户的物品。
    """
    # 创建属于普通用户的物品
    user_item = Item(
        title="User Item",
        description="Belongs to test_user",
        owner_id=test_user.id,
    )
    db_session.add(user_item)
    
    # 创建属于超级管理员的物品
    admin_item = Item(
        title="Admin Item",
        description="Belongs to superuser",
        owner_id=test_superuser.id,
    )
    db_session.add(admin_item)
    await db_session.commit()
    
    response = await superuser_client.get("/v1/items/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2  # 2 new items created in this test
    
    titles = [item["title"] for item in data["data"]]
    assert "User Item" in titles
    assert "Admin Item" in titles


@pytest.mark.asyncio
async def test_read_items_unauthorized(client: AsyncClient):
    """
    测试未登录用户无法获取物品列表。
    """
    response = await client.get("/v1/items/")
    
    assert response.status_code in [401, 403]  # OAuth2 returns 401 for missing token


# ======================== 获取单个物品测试 ========================

@pytest.mark.asyncio
async def test_read_item_by_id_owner(
    authorized_client: AsyncClient,
    test_item: Item
):
    """
    测试物品所有者可以获取自己的物品。
    """
    response = await authorized_client.get(f"/v1/items/{test_item.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_item.id)
    assert data["title"] == test_item.title
    assert data["owner_id"] == str(test_item.owner_id)


@pytest.mark.asyncio
async def test_read_item_by_id_not_found(authorized_client: AsyncClient):
    """
    测试获取不存在的物品返回 404。
    """
    fake_id = uuid.uuid4()
    response = await authorized_client.get(f"/v1/items/{fake_id}")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]


@pytest.mark.asyncio
async def test_read_item_by_id_other_user(
    authorized_client: AsyncClient,
    db_session: AsyncSession
):
    """
    测试普通用户无法获取其他用户的物品。
    """
    # 创建另一个用户和其物品
    other_user = User(
        email="other_item@example.com",
        hashed_password="hashed_password",
        full_name="Other User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(other_user)
    await db_session.commit()
    
    other_item = Item(
        title="Other User's Item",
        description="This belongs to other user",
        owner_id=other_user.id,
    )
    db_session.add(other_item)
    await db_session.commit()
    
    response = await authorized_client.get(f"/v1/items/{other_item.id}")
    
    assert response.status_code == 403
    data = response.json()
    assert "Not enough permissions" in data["detail"]


@pytest.mark.asyncio
async def test_read_item_by_id_superuser_can_access_any(
    superuser_client: AsyncClient,
    test_item: Item
):
    """
    测试超级管理员可以获取任何物品。
    """
    response = await superuser_client.get(f"/v1/items/{test_item.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_item.id)


# ======================== 创建物品测试 ========================

@pytest.mark.asyncio
async def test_create_item_success(
    authorized_client: AsyncClient,
    test_user: User
):
    """
    测试成功创建物品。
    """
    response = await authorized_client.post(
        "/v1/items/",
        json={
            "title": "New Item",
            "description": "A new test item",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Item"
    assert data["description"] == "A new test item"
    assert data["owner_id"] == str(test_user.id)
    assert "id" in data


@pytest.mark.asyncio
async def test_create_item_validation_error(authorized_client: AsyncClient):
    """
    测试创建物品时验证失败（缺少必填字段）。
    """
    response = await authorized_client.post(
        "/v1/items/",
        json={
            "description": "Missing title",
        },
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_item_empty_title(authorized_client: AsyncClient):
    """
    测试创建物品时标题为空失败。
    """
    response = await authorized_client.post(
        "/v1/items/",
        json={
            "title": "",  # 空标题
            "description": "Description",
        },
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_item_unauthorized(client: AsyncClient):
    """
    测试未登录用户无法创建物品。
    """
    response = await client.post(
        "/v1/items/",
        json={
            "title": "New Item",
            "description": "Description",
        },
    )
    
    assert response.status_code in [401, 403]  # OAuth2 returns 401 for missing token


# ======================== 更新物品测试 ========================

@pytest.mark.asyncio
async def test_update_item_success(
    authorized_client: AsyncClient,
    test_item: Item
):
    """
    测试成功更新自己的物品。
    """
    response = await authorized_client.put(
        f"/v1/items/{test_item.id}",
        json={
            "title": "Updated Title",
            "description": "Updated description",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated description"
    assert data["id"] == str(test_item.id)


@pytest.mark.asyncio
async def test_update_item_partial(
    authorized_client: AsyncClient,
    test_item: Item
):
    """
    测试部分更新物品（只更新描述）。
    """
    response = await authorized_client.put(
        f"/v1/items/{test_item.id}",
        json={
            "description": "Only description updated",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    # 标题应该保持不变
    assert data["title"] == test_item.title
    assert data["description"] == "Only description updated"


@pytest.mark.asyncio
async def test_update_item_not_found(authorized_client: AsyncClient):
    """
    测试更新不存在的物品返回 404。
    """
    fake_id = uuid.uuid4()
    response = await authorized_client.put(
        f"/v1/items/{fake_id}",
        json={
            "title": "Updated Title",
        },
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_item_other_user(
    authorized_client: AsyncClient,
    db_session: AsyncSession
):
    """
    测试普通用户无法更新其他用户的物品。
    """
    # 创建另一个用户和其物品
    other_user = User(
        email="other_update@example.com",
        hashed_password="hashed_password",
        full_name="Other User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(other_user)
    await db_session.commit()
    
    other_item = Item(
        title="Other's Item",
        description="Belongs to other",
        owner_id=other_user.id,
    )
    db_session.add(other_item)
    await db_session.commit()
    
    response = await authorized_client.put(
        f"/v1/items/{other_item.id}",
        json={
            "title": "Trying to update",
        },
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_item_superuser_can_update_any(
    superuser_client: AsyncClient,
    test_item: Item
):
    """
    测试超级管理员可以更新任何物品。
    """
    response = await superuser_client.put(
        f"/v1/items/{test_item.id}",
        json={
            "title": "Updated by Admin",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated by Admin"


# ======================== 删除物品测试 ========================

@pytest.mark.asyncio
async def test_delete_item_success(
    authorized_client: AsyncClient,
    test_item: Item
):
    """
    测试成功删除自己的物品。
    """
    response = await authorized_client.delete(f"/v1/items/{test_item.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]


@pytest.mark.asyncio
async def test_delete_item_not_found(authorized_client: AsyncClient):
    """
    测试删除不存在的物品返回 404。
    """
    fake_id = uuid.uuid4()
    response = await authorized_client.delete(f"/v1/items/{fake_id}")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_other_user(
    authorized_client: AsyncClient,
    db_session: AsyncSession
):
    """
    测试普通用户无法删除其他用户的物品。
    """
    # 创建另一个用户和其物品
    other_user = User(
        email="other_delete@example.com",
        hashed_password="hashed_password",
        full_name="Other User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(other_user)
    await db_session.commit()
    
    other_item = Item(
        title="Other's Item to Delete",
        description="Belongs to other",
        owner_id=other_user.id,
    )
    db_session.add(other_item)
    await db_session.commit()
    
    response = await authorized_client.delete(f"/v1/items/{other_item.id}")
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_item_superuser_can_delete_any(
    superuser_client: AsyncClient,
    db_session: AsyncSession,
    test_user: User
):
    """
    测试超级管理员可以删除任何物品。
    """
    # 创建一个物品让超级管理员删除
    item_to_delete = Item(
        title="Item to be deleted by admin",
        description="This will be deleted",
        owner_id=test_user.id,
    )
    db_session.add(item_to_delete)
    await db_session.commit()
    
    response = await superuser_client.delete(f"/v1/items/{item_to_delete.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]


@pytest.mark.asyncio
async def test_delete_item_unauthorized(client: AsyncClient, test_item: Item):
    """
    测试未登录用户无法删除物品。
    """
    response = await client.delete(f"/v1/items/{test_item.id}")
    
    assert response.status_code in [401, 403]  # OAuth2 returns 401 for missing token
