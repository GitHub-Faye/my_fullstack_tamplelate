"""
Task 审计日志记录集成测试

验证每个关键业务操作都正确记录审计日志。
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    AuditLog, Task, TaskStatus, TaskType, User, UserRoleType,
)
from app.core.security import get_password_hash, create_access_token


async def _create_user_with_role(
    session: AsyncSession,
    role_type: UserRoleType,
    full_name: str,
    scopes: list,
) -> User:
    from app.core.models import Role, RoleScope, UserRole
    user = User(
        email=f"{role_type.value}_{uuid.uuid4()}@test.com",
        hashed_password=get_password_hash("test"),
        full_name=full_name,
        role=role_type,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    role = Role(name=f"role_{role_type.value}_{uuid.uuid4()}")
    session.add(role)
    await session.commit()
    session.add(UserRole(user_id=user.id, role_id=role.id))
    for scope in scopes:
        session.add(RoleScope(scope=scope.value, role_id=role.id))
    await session.commit()
    return user


async def create_admin(session: AsyncSession) -> User:
    from app.core.scopes import TaskScope, UserScope
    return await _create_user_with_role(session, UserRoleType.ADMIN, "测试管理员", [
        TaskScope.ADMIN, TaskScope.APPROVE, TaskScope.CONVERT, TaskScope.REASSIGN, UserScope.READ,
    ])


async def create_pm(session: AsyncSession) -> User:
    from app.core.scopes import TaskScope, ReportScope, ClientResourceScope, SalaryScope
    return await _create_user_with_role(session, UserRoleType.PM, "测试PM", [
        TaskScope.READ, TaskScope.CREATE, TaskScope.UPDATE,
        ReportScope.READ, ClientResourceScope.READ, ClientResourceScope.CREATE, SalaryScope.READ,
    ])


async def create_engineer(session: AsyncSession) -> User:
    from app.core.scopes import TaskScope, BidScope, ReportScope, StarPointScope, SalaryScope
    return await _create_user_with_role(session, UserRoleType.ENGINEER, "测试工程师", [
        TaskScope.READ, BidScope.CREATE, BidScope.UPDATE,
        ReportScope.CREATE, ReportScope.READ, StarPointScope.READ, SalaryScope.READ,
    ])


def _token(user: User) -> str:
    return create_access_token(subject=str(user.id), expires_delta=timedelta(minutes=30))


@pytest.mark.asyncio
async def test_audit_log_on_task_create(client: AsyncClient, db_session: AsyncSession):
    """PM 创建任务时记录审计日志"""
    pm = await create_pm(db_session)
    token = _token(pm)

    response = await client.post(
        "/v1/tasks/",
        json={"name": "审计日志测试任务", "description": "测试", "task_type": "normal"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    task_id = response.json()["id"]

    # 验证审计日志已记录
    log_response = await client.get(
        f"/v1/audit-logs/?action=task.create",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert log_response.status_code == 200
    logs = log_response.json()
    assert logs["count"] >= 1, f"Expected at least 1 audit log with action=task.create, got {logs}"
    assert logs["data"][0]["action"] == "task.create"


@pytest.mark.asyncio
async def test_audit_log_on_task_reject(client: AsyncClient, db_session: AsyncSession):
    """管理员驳回任务时记录审计日志"""
    admin = await create_admin(db_session)
    pm = await create_pm(db_session)

    task = Task(name="待驳回任务", status=TaskStatus.UNCONFIRMED, pm_id=pm.id, task_type=TaskType.NORMAL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    token = _token(admin)
    response = await client.post(
        f"/v1/tasks/{task.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    log_response = await client.get(
        f"/v1/audit-logs/?action=task.reject",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert log_response.status_code == 200
    logs = log_response.json()
    assert logs["count"] >= 1


@pytest.mark.asyncio
async def test_audit_log_on_task_publish(client: AsyncClient, db_session: AsyncSession):
    """管理员发布任务时记录审计日志"""
    admin = await create_admin(db_session)
    pm = await create_pm(db_session)

    task = Task(name="待发布任务", status=TaskStatus.UNCONFIRMED, pm_id=pm.id, task_type=TaskType.NORMAL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    token = _token(admin)
    response = await client.post(
        f"/v1/tasks/{task.id}/publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    log_response = await client.get(
        f"/v1/audit-logs/?action=task.publish",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert log_response.status_code == 200
    logs = log_response.json()
    assert logs["count"] >= 1


@pytest.mark.asyncio
async def test_audit_log_on_task_convert_type(client: AsyncClient, db_session: AsyncSession):
    """管理员转换任务类型时记录审计日志"""
    admin = await create_admin(db_session)
    pm = await create_pm(db_session)

    task = Task(name="类型转换测试", status=TaskStatus.UNCONFIRMED, pm_id=pm.id, task_type=TaskType.NORMAL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    token = _token(admin)
    response = await client.post(
        f"/v1/tasks/{task.id}/convert-urgent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    log_response = await client.get(
        f"/v1/audit-logs/?action=task.convert_type",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert log_response.status_code == 200
    logs = log_response.json()
    assert logs["count"] >= 1


@pytest.mark.asyncio
async def test_audit_log_on_task_reassign(client: AsyncClient, db_session: AsyncSession):
    """管理员改派任务时记录审计日志"""
    admin = await create_admin(db_session)
    pm = await create_pm(db_session)
    engineer = await create_engineer(db_session)

    task = Task(name="改派测试", status=TaskStatus.PENDING_START, pm_id=pm.id, engineer_id=engineer.id, task_type=TaskType.NORMAL)
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    token = _token(admin)
    response = await client.post(
        f"/v1/tasks/{task.id}/reassign",
        json={"new_engineer_id": str(engineer.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    log_response = await client.get(
        f"/v1/audit-logs/?action=task.reassign",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert log_response.status_code == 200
    logs = log_response.json()
    assert logs["count"] >= 1


@pytest.mark.asyncio
async def test_audit_log_on_user_management(client: AsyncClient, db_session: AsyncSession):
    """管理员创建用户时记录审计日志"""
    from app.core.scopes import UserScope
    admin = await _create_user_with_role(db_session, UserRoleType.ADMIN, "用户管理员", [
        UserScope.READ, UserScope.CREATE, UserScope.UPDATE, UserScope.DELETE, UserScope.ADMIN,
    ])
    token = _token(admin)

    response = await client.post(
        "/v1/admin/users",
        json={
            "email": f"newuser_{uuid.uuid4()}@test.com",
            "password": "testpassword123",
            "full_name": "新用户",
            "role": "engineer",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    user_id = response.json()["id"]

    log_response = await client.get(
        f"/v1/audit-logs/?action=user.create",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert log_response.status_code == 200
    logs = log_response.json()
    assert logs["count"] >= 1


@pytest.mark.asyncio
async def test_audit_log_on_salary_update(client: AsyncClient, db_session: AsyncSession):
    """管理员更新工资参数时记录审计日志"""
    from app.core.scopes import SalaryScope
    admin = await _create_user_with_role(db_session, UserRoleType.ADMIN, "工资管理员", [SalaryScope.ADMIN])
    engineer = await create_engineer(db_session)

    token = _token(admin)
    response = await client.put(
        f"/v1/salaries/users/{engineer.id}/params",
        json={"S0": 8000, "H0": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    log_response = await client.get(
        f"/v1/audit-logs/?action=salary.update",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert log_response.status_code == 200
    logs = log_response.json()
    assert logs["count"] >= 1