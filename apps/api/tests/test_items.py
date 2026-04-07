"""
Tests for item management endpoints.

Covers:
- List items (/items/)
- Get item by ID (/items/{id})
- Create item (/items/)
- Update item (/items/{id})
- Delete item (/items/{id})
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Item, User
from app.domains.item.schemas import ItemCreate


class TestListItems:
    """Tests for GET /items/ endpoint."""

    async def test_list_items_empty(self, authorized_client: AsyncClient):
        """Test listing items when user has no items."""
        response = await authorized_client.get("/v1/items/")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["count"] == 0

    async def test_list_items_with_data(self, authorized_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test listing items when user has items."""
        # Create some items for the user
        from app.core.models import Item
        item1 = Item(title="Item 1", description="Description 1", owner_id=normal_user.id)
        item2 = Item(title="Item 2", description="Description 2", owner_id=normal_user.id)
        db_session.add(item1)
        db_session.add(item2)
        await db_session.commit()

        response = await authorized_client.get("/v1/items/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["data"]) == 2
        assert data["data"][0]["title"] in ["Item 1", "Item 2"]

    async def test_list_items_as_superuser_sees_all(self, superuser_client: AsyncClient, normal_user: User, superuser: User, db_session: AsyncSession):
        """Test superuser can see all items."""
        from app.core.models import Item
        # Create item for normal user
        item1 = Item(title="User Item", description="User Description", owner_id=normal_user.id)
        # Create item for superuser
        item2 = Item(title="Superuser Item", description="Superuser Description", owner_id=superuser.id)
        db_session.add(item1)
        db_session.add(item2)
        await db_session.commit()

        response = await superuser_client.get("/v1/items/")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["data"]) == 2

    async def test_list_items_pagination(self, authorized_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test listing items with pagination."""
        from app.core.models import Item
        # Create multiple items
        for i in range(5):
            item = Item(title=f"Item {i}", description=f"Description {i}", owner_id=normal_user.id)
            db_session.add(item)
        await db_session.commit()

        response = await authorized_client.get("/v1/items/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["count"] == 5

    async def test_list_items_unauthorized(self, client: AsyncClient):
        """Test listing items without token returns 401."""
        response = await client.get("/v1/items/")
        assert response.status_code == 401


class TestGetItem:
    """Tests for GET /items/{id} endpoint."""

    async def test_get_item_success(self, authorized_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test getting an item by ID."""
        from app.core.models import Item
        item = Item(title="Test Item", description="Test Description", owner_id=normal_user.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await authorized_client.get(f"/v1/items/{item.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Item"
        assert data["description"] == "Test Description"
        assert data["id"] == str(item.id)
        assert data["owner_id"] == str(normal_user.id)

    async def test_get_item_not_found(self, authorized_client: AsyncClient):
        """Test getting non-existent item returns 404."""
        fake_id = uuid.uuid4()
        response = await authorized_client.get(f"/v1/items/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    async def test_get_item_other_user_forbidden(self, authorized_client: AsyncClient, superuser: User, db_session: AsyncSession):
        """Test getting another user's item returns 403."""
        from app.core.models import Item
        # Create item owned by superuser
        item = Item(title="Superuser Item", description="Secret", owner_id=superuser.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await authorized_client.get(f"/v1/items/{item.id}")
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    async def test_get_item_as_superuser_can_access_any(self, superuser_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test superuser can access any item."""
        from app.core.models import Item
        item = Item(title="User Item", description="User Description", owner_id=normal_user.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await superuser_client.get(f"/v1/items/{item.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "User Item"

    async def test_get_item_unauthorized(self, client: AsyncClient):
        """Test getting item without token returns 401."""
        fake_id = uuid.uuid4()
        response = await client.get(f"/v1/items/{fake_id}")
        assert response.status_code == 401


class TestCreateItem:
    """Tests for POST /items/ endpoint."""

    async def test_create_item_success(self, authorized_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test creating an item successfully."""
        response = await authorized_client.post(
            "/v1/items/",
            json={
                "title": "New Item",
                "description": "New Description",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Item"
        assert data["description"] == "New Description"
        assert data["owner_id"] == str(normal_user.id)
        assert "id" in data
        assert "created_at" in data

    async def test_create_item_minimal(self, authorized_client: AsyncClient, normal_user: User):
        """Test creating an item with minimal data (title only)."""
        response = await authorized_client.post(
            "/v1/items/",
            json={
                "title": "Minimal Item",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Minimal Item"
        assert data["description"] is None

    async def test_create_item_validation_error(self, authorized_client: AsyncClient):
        """Test creating an item with invalid data returns 422."""
        response = await authorized_client.post(
            "/v1/items/",
            json={
                "title": "",  # Empty title should fail
            },
        )
        assert response.status_code == 422

    async def test_create_item_unauthorized(self, client: AsyncClient):
        """Test creating item without token returns 401."""
        response = await client.post(
            "/v1/items/",
            json={
                "title": "New Item",
                "description": "New Description",
            },
        )
        assert response.status_code == 401


class TestUpdateItem:
    """Tests for PUT /items/{id} endpoint."""

    async def test_update_item_success(self, authorized_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test updating an item successfully."""
        from app.core.models import Item
        item = Item(title="Original Title", description="Original Description", owner_id=normal_user.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await authorized_client.put(
            f"/v1/items/{item.id}",
            json={
                "title": "Updated Title",
                "description": "Updated Description",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated Description"
        assert data["id"] == str(item.id)

    async def test_update_item_partial(self, authorized_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test updating only title of an item."""
        from app.core.models import Item
        item = Item(title="Original Title", description="Keep This", owner_id=normal_user.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await authorized_client.put(
            f"/v1/items/{item.id}",
            json={
                "title": "Updated Title",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        # Description should remain unchanged
        assert data["description"] == "Keep This"

    async def test_update_item_not_found(self, authorized_client: AsyncClient):
        """Test updating non-existent item returns 404."""
        fake_id = uuid.uuid4()
        response = await authorized_client.put(
            f"/v1/items/{fake_id}",
            json={
                "title": "Updated Title",
            },
        )
        assert response.status_code == 404

    async def test_update_item_other_user_forbidden(self, authorized_client: AsyncClient, superuser: User, db_session: AsyncSession):
        """Test updating another user's item returns 403."""
        from app.core.models import Item
        item = Item(title="Superuser Item", description="Secret", owner_id=superuser.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await authorized_client.put(
            f"/v1/items/{item.id}",
            json={
                "title": "Hacked Title",
            },
        )
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    async def test_update_item_as_superuser_can_update_any(self, superuser_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test superuser can update any item."""
        from app.core.models import Item
        item = Item(title="User Item", description="User Description", owner_id=normal_user.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await superuser_client.put(
            f"/v1/items/{item.id}",
            json={
                "title": "Updated By Superuser",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated By Superuser"

    async def test_update_item_unauthorized(self, client: AsyncClient):
        """Test updating item without token returns 401."""
        fake_id = uuid.uuid4()
        response = await client.put(
            f"/v1/items/{fake_id}",
            json={
                "title": "Updated Title",
            },
        )
        assert response.status_code == 401


class TestDeleteItem:
    """Tests for DELETE /items/{id} endpoint."""

    async def test_delete_item_success(self, authorized_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test deleting an item successfully."""
        from app.core.models import Item
        item = Item(title="Item to Delete", description="Will be deleted", owner_id=normal_user.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)
        item_id = item.id

        response = await authorized_client.delete(f"/v1/items/{item_id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify item was deleted
        result = await db_session.get(Item, item_id)
        assert result is None

    async def test_delete_item_not_found(self, authorized_client: AsyncClient):
        """Test deleting non-existent item returns 404."""
        fake_id = uuid.uuid4()
        response = await authorized_client.delete(f"/v1/items/{fake_id}")
        assert response.status_code == 404

    async def test_delete_item_other_user_forbidden(self, authorized_client: AsyncClient, superuser: User, db_session: AsyncSession):
        """Test deleting another user's item returns 403."""
        from app.core.models import Item
        item = Item(title="Superuser Item", description="Secret", owner_id=superuser.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)

        response = await authorized_client.delete(f"/v1/items/{item.id}")
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]

    async def test_delete_item_as_superuser_can_delete_any(self, superuser_client: AsyncClient, normal_user: User, db_session: AsyncSession):
        """Test superuser can delete any item."""
        from app.core.models import Item
        item = Item(title="User Item", description="User Description", owner_id=normal_user.id)
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)
        item_id = item.id

        response = await superuser_client.delete(f"/v1/items/{item_id}")
        assert response.status_code == 200

        # Verify item was deleted
        result = await db_session.get(Item, item_id)
        assert result is None

    async def test_delete_item_unauthorized(self, client: AsyncClient):
        """Test deleting item without token returns 401."""
        fake_id = uuid.uuid4()
        response = await client.delete(f"/v1/items/{fake_id}")
        assert response.status_code == 401
