"""
客资管理 API 集成测试

测试 PM 客资管理 API：
- POST /client-resources — PM 录入客资
- GET /client-resources — PM 查看自己的客资历史
- GET /client-resources/admin — 管理员查看所有 PM 汇总
- 权限控制（PM 可录入/查看自己的，管理员查看所有）
"""

import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    User,
    UserRoleType,
    Role,
    RoleScope,
    UserRole,
    ClientResource,
)
from app.core.scopes import ClientResourceScope
from app.core.security import create_access_token
from datetime import timedelta


pytestmark = pytest.mark.asyncio


async def _create_test_pm(db_session: AsyncSession) -> User:
    """创建测试 PM 用户（含 client-resource scope）"""
    pm = User(
        email=f"pm_cr_{uuid.uuid4().hex[:8]}@test.com",
        hashed_password="hashed",
        full_name="Test PM",
        role=UserRoleType.PM,
        is_active=True,
        baseline_client_count=100,
    )
    db_session.add(pm)
    await db_session.commit()

    role = Role(name=f"pm_cr_role_{uuid.uuid4().hex[:8]}")
    db_session.add(role)
    await db_session.commit()

    user_role = UserRole(user_id=pm.id, role_id=role.id)
    db_session.add(user_role)

    # 授予 client-resource scope
    for scope in [ClientResourceScope.READ, ClientResourceScope.CREATE]:
        rs = RoleScope(role_id=role.id, scope=scope.value)
        db_session.add(rs)

    await db_session.commit()
    return pm


async def _create_test_admin(db_session: AsyncSession) -> User:
    """创建测试管理员用户"""
    admin = User(
        email=f"admin_cr_{uuid.uuid4().hex[:8]}@test.com",
        hashed_password="hashed",
        full_name="Test Admin",
        role=UserRoleType.ADMIN,
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    await db_session.commit()
    return admin


async def _create_test_engineer(db_session: AsyncSession) -> User:
    """创建测试工程师用户（无客资权限）"""
    eng = User(
        email=f"eng_cr_{uuid.uuid4().hex[:8]}@test.com",
        hashed_password="hashed",
        full_name="Test Engineer",
        role=UserRoleType.ENGINEER,
        is_active=True,
    )
    db_session.add(eng)
    await db_session.commit()
    return eng


@pytest_asyncio.fixture
async def pm_user(db_session: AsyncSession) -> User:
    return await _create_test_pm(db_session)


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    return await _create_test_admin(db_session)


@pytest_asyncio.fixture
async def engineer_user(db_session: AsyncSession) -> User:
    return await _create_test_engineer(db_session)


@pytest_asyncio.fixture
async def pm_token(pm_user: User) -> str:
    return create_access_token(subject=str(pm_user.id), expires_delta=timedelta(minutes=30))


@pytest_asyncio.fixture
async def admin_token(admin_user: User) -> str:
    return create_access_token(subject=str(admin_user.id), expires_delta=timedelta(minutes=30))


@pytest_asyncio.fixture
async def engineer_token(engineer_user: User) -> str:
    return create_access_token(subject=str(engineer_user.id), expires_delta=timedelta(minutes=30))


class TestClientResourceAPI:
    """客资管理 API 集成测试"""

    BASE = "/v1/client-resources"

    async def _create_sample_resource(
        self, db_session: AsyncSession, pm_id: uuid.UUID
    ) -> ClientResource:
        """创建示例客资记录"""
        resource = ClientResource(
            pm_id=pm_id,
            actual_count=120,
            baseline_count=100,
            date=datetime.fromisoformat("2026-07-18T00:00:00+00:00"),
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)
        return resource

    # ==================== POST /client-resources ====================

    async def test_create_client_resource(
        self, client: AsyncClient, pm_token: str, db_session: AsyncSession
    ):
        """PM 成功录入客资"""
        payload = {
            "actual_count": 150,
            "date": "2026-07-18",
        }
        response = await client.post(
            self.BASE,
            json=payload,
            headers={"Authorization": f"Bearer {pm_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["actual_count"] == 150
        assert data["baseline_count"] == 100
        assert "id" in data
        assert "pm_id" in data

    async def test_create_client_resource_without_baseline(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """PM 未设置基准客资数时返回 400"""
        pm = User(
            email=f"pm_no_baseline_{uuid.uuid4().hex[:8]}@test.com",
            hashed_password="hashed",
            full_name="PM No Baseline",
            role=UserRoleType.PM,
            is_active=True,
            baseline_client_count=None,  # 未设置基准客资数
        )
        db_session.add(pm)
        await db_session.commit()

        role = Role(name=f"pm_role_{uuid.uuid4().hex[:8]}")
        db_session.add(role)
        await db_session.commit()

        user_role = UserRole(user_id=pm.id, role_id=role.id)
        db_session.add(user_role)
        for scope in [ClientResourceScope.READ, ClientResourceScope.CREATE]:
            rs = RoleScope(role_id=role.id, scope=scope.value)
            db_session.add(rs)
        await db_session.commit()

        token = create_access_token(subject=str(pm.id), expires_delta=timedelta(minutes=30))

        payload = {
            "actual_count": 150,
            "date": "2026-07-18",
        }
        response = await client.post(
            self.BASE,
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400

    # ==================== GET /client-resources ====================

    async def test_read_my_resources(
        self, client: AsyncClient, pm_token: str, pm_user: User, db_session: AsyncSession
    ):
        """PM 查看自己的客资历史"""
        await self._create_sample_resource(db_session, pm_user.id)

        response = await client.get(
            self.BASE,
            headers={"Authorization": f"Bearer {pm_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert len(data["data"]) >= 1
        assert data["data"][0]["actual_count"] == 120

    async def test_read_my_resources_empty(
        self, client: AsyncClient, pm_token: str
    ):
        """PM 无客资记录时返回空列表"""
        response = await client.get(
            self.BASE,
            headers={"Authorization": f"Bearer {pm_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["data"] == []

    # ==================== 权限控制 ====================

    async def test_engineer_cannot_create_resource(
        self, client: AsyncClient, engineer_token: str
    ):
        """工程师无法录入客资"""
        payload = {
            "actual_count": 100,
            "date": "2026-07-18",
        }
        response = await client.post(
            self.BASE,
            json=payload,
            headers={"Authorization": f"Bearer {engineer_token}"},
        )
        assert response.status_code == 403

    async def test_engineer_cannot_read_resources(
        self, client: AsyncClient, engineer_token: str
    ):
        """工程师无法查看客资"""
        response = await client.get(
            self.BASE,
            headers={"Authorization": f"Bearer {engineer_token}"},
        )
        assert response.status_code == 403

    async def test_unauthorized_access(self, client: AsyncClient):
        """未认证用户无法访问"""
        response = await client.get(self.BASE)
        assert response.status_code == 401

    # ==================== 分页 ====================

    async def test_read_resources_pagination(
        self, client: AsyncClient, pm_token: str, pm_user: User, db_session: AsyncSession
    ):
        """分页参数正常工作"""
        for i in range(3):
            resource = ClientResource(
                pm_id=pm_user.id,
                actual_count=100 + i,
                baseline_count=100,
                date=datetime.fromisoformat(f"2026-07-{18 + i}T00:00:00+00:00"),
            )
            db_session.add(resource)
        await db_session.commit()

        response = await client.get(
            f"{self.BASE}?page=1&page_size=2",
            headers={"Authorization": f"Bearer {pm_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 2

    # ==================== GET /client-resources/admin ====================

    async def test_admin_read_summary(
        self, client: AsyncClient, admin_token: str, pm_user: User, db_session: AsyncSession
    ):
        """管理员查看所有 PM 客资汇总"""
        # 创建两条客资记录
        await self._create_sample_resource(db_session, pm_user.id)
        await self._create_sample_resource(db_session, pm_user.id)

        response = await client.get(
            f"{self.BASE}/admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        pm_summary = [s for s in data if s["pm_id"] == str(pm_user.id)]
        assert len(pm_summary) == 1
        assert pm_summary[0]["record_count"] == 2
        assert pm_summary[0]["total_actual"] == 240

    async def test_pm_cannot_read_admin_summary(
        self, client: AsyncClient, pm_token: str
    ):
        """PM 无法查看管理汇总"""
        response = await client.get(
            f"{self.BASE}/admin",
            headers={"Authorization": f"Bearer {pm_token}"},
        )
        assert response.status_code == 403

    # ==================== PUT /users/{id}/client-resource-params ====================

    async def test_admin_set_client_resource_params(
        self, client: AsyncClient, admin_token: str, pm_user: User, db_session: AsyncSession
    ):
        """管理员设置 PM 的基准客资数"""
        response = await client.put(
            f"/v1/admin/users/{pm_user.id}/client-resource-params",
            json={"baseline_client_count": 200},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["baseline_client_count"] == 200

    async def test_set_params_on_non_pm_fails(
        self, client: AsyncClient, admin_token: str, engineer_user: User
    ):
        """设置非 PM 用户的客资参数返回 403"""
        response = await client.put(
            f"/v1/admin/users/{engineer_user.id}/client-resource-params",
            json={"baseline_client_count": 200},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 403