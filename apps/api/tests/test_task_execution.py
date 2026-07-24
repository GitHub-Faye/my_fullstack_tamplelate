"""
任务执行 API 端点测试模块

测试工程师任务执行的完整流程：
- 启动任务
- 拒绝任务
- 申请暂停
- 恢复任务
- 完成任务
- 管理员审批暂停
- 管理员改派任务
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.models import (
    Task,
    TaskStatus,
    User,
    UserRoleType,
    Bid,
)
from app.core.security import get_password_hash, create_access_token
from tests.utils import create_test_user, create_test_token, get_auth_headers


async def create_test_task(
    session: AsyncSession,
    pm: User,
    engineer: User | None = None,
    status: TaskStatus = TaskStatus.PENDING_START,
) -> Task:
    """创建测试任务"""
    task = Task(
        name="Test Task for Execution",
        description="Test task description",
        status=status,
        pm_id=pm.id,
        engineer_id=engineer.id if engineer else None,
        task_type="normal",
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


class TestTaskExecution:
    """任务执行测试类"""

    @pytest.mark.asyncio
    async def test_start_task_success(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师成功启动任务
        - 任务状态从 PENDING_START 变为 IN_PROGRESS
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_start@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()
        await db_session.refresh(pm)

        engineer = await create_test_user(
            db_session,
            email="eng_start@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()
        await db_session.refresh(engineer)

        # 2. 创建待启动任务
        task = await create_test_task(
            db_session, pm, engineer, status=TaskStatus.PENDING_START
        )

        # 3. 工程师启动任务
        token = create_test_token(engineer.id)
        response = await client.post(
            f"/v1/tasks/{task.id}/start",
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == TaskStatus.IN_PROGRESS.value

        # 5. 验证数据库
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_start_task_not_assigned(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师启动未分配给自己的任务
        - 应返回 403 错误
        """
        # 1. 创建 PM 和两个工程师
        pm = await create_test_user(
            db_session,
            email="pm_not_assigned@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer1 = await create_test_user(
            db_session,
            email="eng1_not_assigned@example.com",
            is_superuser=False,
        )
        engineer1.role = UserRoleType.ENGINEER
        db_session.add(engineer1)
        await db_session.commit()

        engineer2 = await create_test_user(
            db_session,
            email="eng2_not_assigned@example.com",
            is_superuser=False,
        )
        engineer2.role = UserRoleType.ENGINEER
        db_session.add(engineer2)
        await db_session.commit()

        # 2. 创建分配给 engineer1 的任务
        task = await create_test_task(
            db_session, pm, engineer1, status=TaskStatus.PENDING_START
        )

        # 3. engineer2 尝试启动任务
        token = create_test_token(engineer2.id)
        response = await client.post(
            f"/v1/tasks/{task.id}/start",
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_start_task_wrong_status(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试启动非 PENDING_START 状态的任务
        - 应返回 400 错误
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_wrong_status@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_wrong_status@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        # 2. 创建 IN_PROGRESS 状态的任务
        task = await create_test_task(
            db_session, pm, engineer, status=TaskStatus.IN_PROGRESS
        )

        # 3. 尝试启动任务
        token = create_test_token(engineer.id)
        response = await client.post(
            f"/v1/tasks/{task.id}/start",
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reject_task_success(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师成功拒绝任务
        - 任务重新进入竞价（BIDDING），设置新的竞价截止时间
        - engineer_id 被清空
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_reject@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_reject@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        # 2. 创建待启动任务
        task = await create_test_task(
            db_session, pm, engineer, status=TaskStatus.PENDING_START
        )

        # 3. 工程师拒绝任务
        token = create_test_token(engineer.id)
        response = await client.post(
            f"/v1/tasks/{task.id}/decline",
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        if response.status_code != 200:
            print(f"Response: {response.json()}")
        assert response.status_code == 200

        # 5. 验证数据库
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.status == TaskStatus.BIDDING
        assert updated_task.engineer_id is None
        assert updated_task.bidding_deadline is not None

    @pytest.mark.asyncio
    async def test_pause_request_success(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师成功暂停任务
        - 状态从 IN_PROGRESS 变为 PAUSED
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_pause@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_pause@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        # 2. 创建进行中任务
        task = await create_test_task(
            db_session, pm, engineer, status=TaskStatus.IN_PROGRESS
        )

        # 3. 工程师申请暂停
        token = create_test_token(engineer.id)
        response = await client.post(
            f"/v1/tasks/{task.id}/pause-request",
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        assert response.status_code == 200

        # 5. 验证数据库 - 状态变为 PAUSE_REQUESTED（待审批）
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.status == TaskStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume_task_success(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师成功恢复暂停的任务
        - 任务状态从 PAUSED 变为 IN_PROGRESS
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_resume@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_resume@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        # 2. 创建暂停任务
        task = await create_test_task(
            db_session, pm, engineer, status=TaskStatus.PAUSED
        )

        # 3. 工程师恢复任务
        token = create_test_token(engineer.id)
        response = await client.post(
            f"/v1/tasks/{task.id}/resume",
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        assert response.status_code == 200

        # 5. 验证数据库
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.status == TaskStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_complete_task_success(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师成功完成任务
        - 任务状态从 IN_PROGRESS 变为 COMPLETED
        - 工程师填报工时被记录
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_complete@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_complete@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        # 2. 创建进行中任务
        task = await create_test_task(
            db_session, pm, engineer, status=TaskStatus.IN_PROGRESS
        )

        # 3. 工程师完成任务（T报已从竞价报价同步，无需重复填写）
        token = create_test_token(engineer.id)
        response = await client.post(
            f"/v1/tasks/{task.id}/complete",
            json={},
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        assert response.status_code == 200

        # 5. 验证数据库
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.status == TaskStatus.COMPLETED
        # T_reported 来自竞价报价，不在 complete 时填写
        # 这里 task 没有竞价，T_reported 保持 None

    @pytest.mark.asyncio
    async def test_admin_reassign_task_success(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试管理员改派任务
        - 任务被分配给新工程师
        - 状态变为 PENDING_START
        """
        # 1. 创建 PM、两个工程师和管理员
        pm = await create_test_user(
            db_session,
            email="pm_reassign@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer1 = await create_test_user(
            db_session,
            email="eng1_reassign@example.com",
            is_superuser=False,
        )
        engineer1.role = UserRoleType.ENGINEER
        db_session.add(engineer1)
        await db_session.commit()

        engineer2 = await create_test_user(
            db_session,
            email="eng2_reassign@example.com",
            is_superuser=False,
        )
        engineer2.role = UserRoleType.ENGINEER
        db_session.add(engineer2)
        await db_session.commit()

        admin = await create_test_user(
            db_session,
            email="admin_reassign@example.com",
            is_superuser=True,  # 超级管理员
        )

        # 2. 创建分配给 engineer1 的进行中任务
        task = await create_test_task(
            db_session, pm, engineer1, status=TaskStatus.IN_PROGRESS
        )

        # 3. 管理员改派给 engineer2
        token = create_test_token(admin.id)
        response = await client.post(
            f"/v1/tasks/{task.id}/reassign",
            json={"new_engineer_id": str(engineer2.id)},
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        assert response.status_code == 200

        # 5. 验证数据库
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.engineer_id == engineer2.id
        assert updated_task.status == TaskStatus.PENDING_START
