"""
系统规则 API 集成测试

测试规则配置管理 API：
- 查看规则列表（支持分类过滤）
- 创建规则
- 查看规则详情
- 更新规则
- 删除规则
- 权限控制（仅管理员）
"""

import uuid

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
    SystemRule,
    RuleCategory,
)
from app.core.scopes import RuleScope


pytestmark = pytest.mark.asyncio


async def _create_test_admin(db_session: AsyncSession) -> User:
    """创建测试管理员用户（含 rule:admin scope）"""
    admin = User(
        email=f"admin_rule_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Test Admin",
        role=UserRoleType.ADMIN,
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    await db_session.commit()

    role = Role(name=f"admin_{uuid.uuid4().hex[:8]}")
    db_session.add(role)
    await db_session.commit()

    user_role = UserRole(user_id=admin.id, role_id=role.id)
    db_session.add(user_role)
    await db_session.commit()

    # 授予 rule:admin scope
    scope = RoleScope(role_id=role.id, scope=RuleScope.ADMIN.value)
    db_session.add(scope)
    await db_session.commit()

    return admin


async def _create_test_pm(db_session: AsyncSession) -> User:
    """创建测试 PM（无 rule scope）"""
    pm = User(
        email=f"pm_rule_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Test PM",
        role=UserRoleType.PM,
        is_active=True,
    )
    db_session.add(pm)
    await db_session.commit()

    role = Role(name=f"pm_role_{uuid.uuid4().hex[:8]}")
    db_session.add(role)
    await db_session.commit()

    user_role = UserRole(user_id=pm.id, role_id=role.id)
    db_session.add(user_role)
    await db_session.commit()

    return pm


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    return await _create_test_admin(db_session)


@pytest_asyncio.fixture
async def pm_user(db_session: AsyncSession) -> User:
    return await _create_test_pm(db_session)


@pytest_asyncio.fixture
async def admin_token(admin_user: User) -> str:
    from app.core.security import create_access_token
    from datetime import timedelta
    return create_access_token(subject=str(admin_user.id), expires_delta=timedelta(minutes=30))


@pytest_asyncio.fixture
async def pm_token(pm_user: User) -> str:
    from app.core.security import create_access_token
    from datetime import timedelta
    return create_access_token(subject=str(pm_user.id), expires_delta=timedelta(minutes=30))


class TestSystemRuleAPI:
    """系统规则 API 集成测试"""

    BASE = "/v1/system-rules"

    async def _create_sample_rule(self, db_session: AsyncSession) -> SystemRule:
        """创建示例规则"""
        rule = SystemRule(
            category=RuleCategory.STARPOINT_REWARD,
            name="测试规则",
            applies_to="engineer",
            value='{"test_key": 10}',
            is_public=True,
            is_active=True,
        )
        db_session.add(rule)
        await db_session.commit()
        await db_session.refresh(rule)
        return rule

    # ==================== GET /system-rules ====================

    async def test_read_rules_empty(self, client: AsyncClient, admin_token: str):
        """未创建规则时返回空列表"""
        response = await client.get(
            self.BASE,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["data"] == []

    async def test_read_rules_with_data(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """有规则时返回规则列表"""
        await self._create_sample_rule(db_session)

        response = await client.get(
            self.BASE,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert len(data["data"]) >= 1
        assert data["data"][0]["name"] == "测试规则"

    async def test_read_rules_filter_by_category(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """按分类过滤规则"""
        # 创建两条不同分类的规则
        r1 = SystemRule(
            category=RuleCategory.STARPOINT_REWARD,
            name="星点规则",
            value='{"a": 1}',
        )
        r2 = SystemRule(
            category=RuleCategory.SALARY_FORMULA,
            name="工资规则",
            value='{"b": 2}',
        )
        db_session.add_all([r1, r2])
        await db_session.commit()

        response = await client.get(
            f"{self.BASE}?category=starpoint_reward",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["category"] == "starpoint_reward" for item in data["data"])

    async def test_read_rules_invalid_category(
        self, client: AsyncClient, admin_token: str
    ):
        """无效分类返回 400"""
        response = await client.get(
            f"{self.BASE}?category=invalid_category",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400

    # ==================== POST /system-rules ====================

    async def test_create_rule(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """创建规则成功"""
        payload = {
            "category": "starpoint_reward",
            "name": "新规则",
            "value": '{"bonus": 20}',
        }
        response = await client.post(
            self.BASE,
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新规则"
        assert data["category"] == "starpoint_reward"
        assert data["value"] == '{"bonus": 20}'
        assert data["is_active"] is True
        assert "id" in data

    async def test_create_rule_with_all_fields(
        self, client: AsyncClient, admin_token: str
    ):
        """创建规则时设置所有字段"""
        payload = {
            "category": "salary_formula",
            "name": "全字段规则",
            "applies_to": "engineer",
            "value": '{"formula": "test"}',
            "is_public": True,
            "is_active": False,
        }
        response = await client.post(
            self.BASE,
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["applies_to"] == "engineer"
        assert data["is_active"] is False

    # ==================== GET /system-rules/{id} ====================

    async def test_read_rule(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """查看规则详情"""
        rule = await self._create_sample_rule(db_session)

        response = await client.get(
            f"{self.BASE}/{rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(rule.id)
        assert data["name"] == "测试规则"

    async def test_read_rule_not_found(
        self, client: AsyncClient, admin_token: str
    ):
        """不存在的规则返回 404"""
        response = await client.get(
            f"{self.BASE}/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    # ==================== PUT /system-rules/{id} ====================

    async def test_update_rule(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """更新规则成功"""
        rule = await self._create_sample_rule(db_session)

        response = await client.put(
            f"{self.BASE}/{rule.id}",
            json={"name": "更新后的规则", "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新后的规则"
        assert data["is_active"] is False

    async def test_update_rule_no_fields(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """不传任何更新字段返回 400"""
        rule = await self._create_sample_rule(db_session)

        response = await client.put(
            f"{self.BASE}/{rule.id}",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400

    async def test_update_rule_not_found(
        self, client: AsyncClient, admin_token: str
    ):
        """更新不存在的规则返回 404"""
        response = await client.put(
            f"{self.BASE}/{uuid.uuid4()}",
            json={"name": "新名称"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    # ==================== DELETE /system-rules/{id} ====================

    async def test_delete_rule(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """删除规则成功"""
        rule = await self._create_sample_rule(db_session)

        response = await client.delete(
            f"{self.BASE}/{rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Rule deleted successfully"

        # 验证已删除
        get_response = await client.get(
            f"{self.BASE}/{rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_response.status_code == 404

    async def test_delete_rule_not_found(
        self, client: AsyncClient, admin_token: str
    ):
        """删除不存在的规则返回 404"""
        response = await client.delete(
            f"{self.BASE}/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    # ==================== 权限控制 ====================

    async def test_pm_cannot_read_rules(
        self, client: AsyncClient, pm_token: str
    ):
        """PM 无法读取规则列表"""
        response = await client.get(
            self.BASE,
            headers={"Authorization": f"Bearer {pm_token}"},
        )
        assert response.status_code == 403

    async def test_pm_cannot_create_rule(
        self, client: AsyncClient, pm_token: str
    ):
        """PM 无法创建规则"""
        response = await client.post(
            self.BASE,
            json={"category": "starpoint_reward", "name": "test", "value": "{}"},
            headers={"Authorization": f"Bearer {pm_token}"},
        )
        assert response.status_code == 403

    async def test_unauthorized_access(
        self, client: AsyncClient
    ):
        """未认证用户无法访问"""
        response = await client.get(self.BASE)
        assert response.status_code == 401

    # ==================== 分页 ====================

    async def test_read_rules_pagination(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """分页参数正常工作"""
        # 创建 3 条规则
        for i in range(3):
            rule = SystemRule(
                category=RuleCategory.STARPOINT_REWARD,
                name=f"分页规则{i}",
                value='{"v": 1}',
            )
            db_session.add(rule)
        await db_session.commit()

        # page_size=2, page=1
        response = await client.get(
            f"{self.BASE}?page=1&page_size=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 2

    # ==================== 规则修改历史 ====================

    async def test_audit_log_created_on_create(
        self, client: AsyncClient, admin_token: str
    ):
        """创建规则时自动记录审计日志"""
        payload = {
            "category": "starpoint_reward",
            "name": "审计测试规则",
            "value": '{"test": 1}',
        }
        response = await client.post(
            self.BASE,
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        rule_id = response.json()["id"]

        # 验证审计日志已生成
        logs_response = await client.get(
            f"{self.BASE}/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert logs_response.status_code == 200
        logs_data = logs_response.json()
        assert logs_data["count"] >= 1
        # 找到刚创建的规则对应的日志
        rule_logs = [log for log in logs_data["data"] if log["target_id"] == rule_id]
        assert len(rule_logs) >= 1
        assert rule_logs[0]["action"] == "rule.create"

    async def test_audit_log_created_on_update(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """更新规则时自动记录审计日志"""
        rule = await self._create_sample_rule(db_session)

        response = await client.put(
            f"{self.BASE}/{rule.id}",
            json={"name": "更新后名称", "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        # 验证审计日志
        logs_response = await client.get(
            f"{self.BASE}/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert logs_response.status_code == 200
        logs_data = logs_response.json()
        rule_logs = [log for log in logs_data["data"] if log["target_id"] == str(rule.id) and log["action"] == "rule.update"]
        assert len(rule_logs) >= 1
        assert "changed_fields" in rule_logs[0]["details"]

    async def test_audit_log_created_on_delete(
        self, client: AsyncClient, admin_token: str, db_session: AsyncSession
    ):
        """删除规则时自动记录审计日志"""
        rule = await self._create_sample_rule(db_session)

        response = await client.delete(
            f"{self.BASE}/{rule.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        # 验证审计日志
        logs_response = await client.get(
            f"{self.BASE}/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert logs_response.status_code == 200
        logs_data = logs_response.json()
        rule_logs = [log for log in logs_data["data"] if log["target_id"] == str(rule.id) and log["action"] == "rule.delete"]
        assert len(rule_logs) >= 1

    async def test_audit_logs_pagination(
        self, client: AsyncClient, admin_token: str
    ):
        """审计日志分页正常工作"""
        # 创建多条规则产生审计日志
        for i in range(3):
            payload = {
                "category": "starpoint_reward",
                "name": f"日志测试{i}",
                "value": '{"v": 1}',
            }
            await client.post(
                self.BASE,
                json=payload,
                headers={"Authorization": f"Bearer {admin_token}"},
            )

        # 验证分页
        response = await client.get(
            f"{self.BASE}/audit-logs?page=1&page_size=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 3
        assert len(data["data"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    async def test_pm_cannot_read_audit_logs(
        self, client: AsyncClient, pm_token: str
    ):
        """PM 无法查看规则修改历史"""
        response = await client.get(
            f"{self.BASE}/audit-logs",
            headers={"Authorization": f"Bearer {pm_token}"},
        )
        assert response.status_code == 403