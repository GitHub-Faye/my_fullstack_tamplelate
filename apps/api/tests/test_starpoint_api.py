"""
星点 API 集成测试

测试星点模块的 RESTful API 端点：
- 查看我的星点记录
- 查看我的星点汇总
- 星点排行榜
- 管理员手动调整星点
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User, UserRoleType, StarPointRecord, JudgmentType
from app.core.security import get_password_hash, create_access_token
from tests.conftest import client as async_client_fixture


async def create_test_engineer(session: AsyncSession) -> User:
    """创建测试工程师用户"""
    from app.core.models import Role, RoleScope, UserRole
    from app.core.scopes import StarPointScope, TaskScope, BidScope, ReportScope, SalaryScope

    engineer = User(
        email=f"engineer_starpoint_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Engineer",
        role=UserRoleType.ENGINEER,
        is_active=True,
    )
    session.add(engineer)
    await session.commit()

    # 创建角色并关联 scopes（使用唯一名称避免重复）
    role_name = f"engineer_{uuid.uuid4().hex[:8]}"
    role = Role(name=role_name)
    session.add(role)
    await session.commit()

    user_role = UserRole(user_id=engineer.id, role_id=role.id)
    session.add(user_role)

    for scope in [
        TaskScope.READ,
        BidScope.CREATE, BidScope.UPDATE,
        ReportScope.CREATE, ReportScope.READ,
        StarPointScope.READ,
        SalaryScope.READ,
    ]:
        rs = RoleScope(scope=scope.value, role_id=role.id)
        session.add(rs)

    await session.commit()
    return engineer


async def create_test_admin(session: AsyncSession) -> User:
    """创建测试管理员用户"""
    from app.core.models import Role, RoleScope, UserRole
    from app.core.scopes import (
        TaskScope, ReportScope, StarPointScope, SalaryScope,
        UserScope, BidScope, ClientResourceScope, RuleScope,
    )

    admin = User(
        email=f"admin_starpoint_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Admin",
        role=UserRoleType.ADMIN,
        is_active=True,
    )
    session.add(admin)
    await session.commit()

    role_name = f"admin_{uuid.uuid4().hex[:8]}"
    role = Role(name=role_name)
    session.add(role)
    await session.commit()

    user_role = UserRole(user_id=admin.id, role_id=role.id)
    session.add(user_role)

    for scope in [
        TaskScope.READ, TaskScope.CREATE, TaskScope.UPDATE, TaskScope.ADMIN,
        BidScope.READ,
        ReportScope.READ, ReportScope.ADMIN,
        StarPointScope.READ, StarPointScope.ADMIN,
        SalaryScope.READ, SalaryScope.ADMIN,
        ClientResourceScope.READ,
        UserScope.READ, UserScope.CREATE, UserScope.UPDATE, UserScope.ADMIN,
        RuleScope.ADMIN,
    ]:
        rs = RoleScope(scope=scope.value, role_id=role.id)
        session.add(rs)

    await session.commit()
    return admin


async def create_starpoint_record(
    session: AsyncSession,
    engineer_id: uuid.UUID,
    change_amount: int = 10,
    judgment_type: JudgmentType = JudgmentType.AUTO_RATIO,
) -> StarPointRecord:
    """创建测试星点记录（同时更新工程师星点）"""
    record = StarPointRecord(
        engineer_id=engineer_id,
        task_id=None,
        change_amount=change_amount,
        judgment_type=judgment_type,
        reason="Test starpoint change",
        T_reported=10.0,
        T_actual=9.5,
    )
    session.add(record)

    # 同步更新工程师的 current_starpoint
    engineer = await session.get(User, engineer_id)
    if engineer:
        engineer.current_starpoint += change_amount
        session.add(engineer)

    await session.commit()
    await session.refresh(record)
    return record


class TestStarPointAPIs:

    @pytest.mark.asyncio
    async def test_read_my_starpoints_empty(self, client: AsyncClient, db_session: AsyncSession):
        """测试工程师查看自己的星点记录（无记录时）"""
        engineer = await create_test_engineer(db_session)

        token = create_access_token(
            subject=str(engineer.id),
            expires_delta=timedelta(minutes=30),
        )

        response = await client.get(
            "/v1/starpoints/my",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["data"]) == 0

    @pytest.mark.asyncio
    async def test_read_my_starpoints_with_records(self, client: AsyncClient, db_session: AsyncSession):
        """测试工程师查看自己的星点记录（有记录时）"""
        engineer = await create_test_engineer(db_session)
        await create_starpoint_record(db_session, engineer.id, 10)
        await create_starpoint_record(db_session, engineer.id, -5, JudgmentType.AUTO_THRESHOLD)

        token = create_access_token(
            subject=str(engineer.id),
            expires_delta=timedelta(minutes=30),
        )

        response = await client.get(
            "/v1/starpoints/my",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["data"]) == 2

        # 验证记录内容
        records = data["data"]
        # 最新的记录排前面
        assert records[0]["change_amount"] == -5

    @pytest.mark.asyncio
    async def test_read_my_starpoint_summary(self, client: AsyncClient, db_session: AsyncSession):
        """测试工程师查看自己的星点汇总"""
        engineer = await create_test_engineer(db_session)
        await create_starpoint_record(db_session, engineer.id, 10)

        token = create_access_token(
            subject=str(engineer.id),
            expires_delta=timedelta(minutes=30),
        )

        response = await client.get(
            "/v1/starpoints/my/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_starpoints"] == 10
        assert data["current_month_earned"] == 10
        assert "rank" in data
        # 单个工程师在排行榜前20%，K = 1.1
        assert data["k_coefficient"] == 1.1

    @pytest.mark.asyncio
    async def test_leaderboard(self, client: AsyncClient, db_session: AsyncSession):
        """测试星点排行榜"""
        # 创建两个工程师
        engineer1 = await create_test_engineer(db_session)
        engineer2 = await create_test_engineer(db_session)

        # 给工程师1加更多星点
        await create_starpoint_record(db_session, engineer1.id, 20)
        await create_starpoint_record(db_session, engineer2.id, 10)

        # 使用管理员 token
        admin = await create_test_admin(db_session)
        token = create_access_token(
            subject=str(admin.id),
            expires_delta=timedelta(minutes=30),
        )

        response = await client.get(
            "/v1/starpoints/leaderboard",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 2

        # 工程师1排在工程师2前面（星点更多）
        entries = data["data"]
        # 找到我们的工程师
        e1_entry = next(e for e in entries if e["engineer_id"] == str(engineer1.id))
        e2_entry = next(e for e in entries if e["engineer_id"] == str(engineer2.id))
        assert e1_entry["rank"] < e2_entry["rank"]

    @pytest.mark.asyncio
    async def test_admin_adjust_starpoint(self, client: AsyncClient, db_session: AsyncSession):
        """测试管理员手动调整星点"""
        engineer = await create_test_engineer(db_session)
        admin = await create_test_admin(db_session)

        token = create_access_token(
            subject=str(admin.id),
            expires_delta=timedelta(minutes=30),
        )

        response = await client.post(
            "/v1/starpoints/adjust",
            json={
                "engineer_id": str(engineer.id),
                "change_amount": 50,
                "reason": "Excellent performance bonus",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["change_amount"] == 50
        assert data["reason"] == "Excellent performance bonus"
        assert data["judgment_type"] == JudgmentType.MANUAL.value

        # 验证工程师的星点已更新
        updated_engineer = await db_session.get(User, engineer.id)
        assert updated_engineer.current_starpoint == 50

    @pytest.mark.asyncio
    async def test_non_admin_cannot_adjust_starpoint(self, client: AsyncClient, db_session: AsyncSession):
        """测试非管理员无法调整星点"""
        engineer = await create_test_engineer(db_session)

        token = create_access_token(
            subject=str(engineer.id),
            expires_delta=timedelta(minutes=30),
        )

        response = await client.post(
            "/v1/starpoints/adjust",
            json={
                "engineer_id": str(engineer.id),
                "change_amount": 10,
                "reason": "Self adjustment attempt",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # 工程师没有 starpoint:admin 权限
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, db_session: AsyncSession):
        """测试星点记录分页"""
        engineer = await create_test_engineer(db_session)

        # 创建 5 条记录
        for i in range(5):
            await create_starpoint_record(db_session, engineer.id, 10)

        token = create_access_token(
            subject=str(engineer.id),
            expires_delta=timedelta(minutes=30),
        )

        # 测试第一页（每页2条）
        response = await client.get(
            "/v1/starpoints/my?page=1&page_size=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["count"] == 5
        assert data["total_pages"] == 3

        # 测试第二页
        response = await client.get(
            "/v1/starpoints/my?page=2&page_size=2",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
