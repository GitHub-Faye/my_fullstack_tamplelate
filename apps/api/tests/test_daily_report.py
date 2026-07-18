"""
日报 API 端点测试模块

测试工程师日报填报的完整流程：
- 填写日报
- 查看日报列表
- 查看日报详情
- 更新日报
- 权限控制
"""

import uuid
from datetime import datetime, timezone, date

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.models import (
    Task,
    TaskStatus,
    User,
    UserRoleType,
    DailyReport,
    ReportStage,
)
from app.core.security import get_password_hash, create_access_token
from tests.utils import create_test_user, create_test_token, get_auth_headers


async def create_test_task(
    session: AsyncSession,
    pm: User,
    engineer: User | None = None,
    status: TaskStatus = TaskStatus.IN_PROGRESS,
) -> Task:
    """创建测试任务"""
    task = Task(
        name="Test Task for Daily Report",
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


class TestDailyReport:
    """日报测试类"""

    @pytest.mark.asyncio
    async def test_create_daily_report_success(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师成功填写日报
        - 日报被创建
        - 任务 T_actual 自动累加
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_report@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()
        await db_session.refresh(pm)

        engineer = await create_test_user(
            db_session,
            email="eng_report@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()
        await db_session.refresh(engineer)

        # 2. 创建进行中任务
        task = await create_test_task(db_session, pm, engineer)

        # 3. 工程师填写日报
        token = create_test_token(engineer.id)
        response = await client.post(
            "/v1/daily-reports/",
            json={
                "task_id": str(task.id),
                "today_hours": 8.0,
                "current_stage": "developing",
                "progress": "完成80%",
                "summary": "今日完成核心功能开发",
            },
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["today_hours"] == 8.0
        assert data["current_stage"] == "developing"

        # 5. 验证数据库
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.T_actual == 8.0

    @pytest.mark.asyncio
    async def test_create_daily_report_not_assigned(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师为未分配给自己的任务填写日报
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
        task = await create_test_task(db_session, pm, engineer1)

        # 3. engineer2 尝试填写日报
        token = create_test_token(engineer2.id)
        response = await client.post(
            "/v1/daily-reports/",
            json={
                "task_id": str(task.id),
                "today_hours": 8.0,
                "current_stage": "developing",
            },
            headers=get_auth_headers(token),
        )

        # 4. 验证响应
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_daily_report_duplicate(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师重复填写同一天的日报
        - 应返回 400 错误
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_duplicate@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_duplicate@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        # 2. 创建任务
        task = await create_test_task(db_session, pm, engineer)

        # 3. 工程师填写日报
        token = create_test_token(engineer.id)
        response = await client.post(
            "/v1/daily-reports/",
            json={
                "task_id": str(task.id),
                "today_hours": 8.0,
                "current_stage": "developing",
            },
            headers=get_auth_headers(token),
        )
        assert response.status_code == 200

        # 4. 再次填写同一天的日报
        response = await client.post(
            "/v1/daily-reports/",
            json={
                "task_id": str(task.id),
                "today_hours": 4.0,
                "current_stage": "testing",
            },
            headers=get_auth_headers(token),
        )

        # 5. 验证响应
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_read_daily_reports_list(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试查看日报列表
        - 工程师只能看自己的日报
        - 管理员可看所有日报
        """
        # 1. 创建 PM、工程师和管理员
        pm = await create_test_user(
            db_session,
            email="pm_list@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_list@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        admin = await create_test_user(
            db_session,
            email="admin_list@example.com",
            is_superuser=True,
        )

        # 2. 创建任务和日报
        task = await create_test_task(db_session, pm, engineer)

        report = DailyReport(
            today_hours=8.0,
            current_stage=ReportStage.DEVELOPING,
            engineer_id=engineer.id,
            task_id=task.id,
            report_date=datetime.now(timezone.utc),
        )
        db_session.add(report)
        await db_session.commit()

        # 3. 工程师查看日报列表
        token = create_test_token(engineer.id)
        response = await client.get(
            "/v1/daily-reports/",
            headers=get_auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

        # 4. 管理员查看日报列表
        token = create_test_token(admin.id)
        response = await client.get(
            "/v1/daily-reports/",
            headers=get_auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

    @pytest.mark.asyncio
    async def test_read_daily_report_detail(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试查看日报详情
        - 工程师只能看自己的日报
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_detail@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_detail@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        # 2. 创建任务和日报
        task = await create_test_task(db_session, pm, engineer)

        report = DailyReport(
            today_hours=8.0,
            current_stage=ReportStage.DEVELOPING,
            engineer_id=engineer.id,
            task_id=task.id,
            report_date=datetime.now(timezone.utc),
        )
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)

        # 3. 工程师查看日报详情
        token = create_test_token(engineer.id)
        response = await client.get(
            f"/v1/daily-reports/{report.id}",
            headers=get_auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["today_hours"] == 8.0

    @pytest.mark.asyncio
    async def test_update_daily_report_success(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试工程师更新日报
        - 只能更新自己的日报
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(
            db_session,
            email="pm_update@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_update@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        # 2. 创建任务和日报
        task = await create_test_task(db_session, pm, engineer)

        report = DailyReport(
            today_hours=8.0,
            current_stage=ReportStage.DEVELOPING,
            engineer_id=engineer.id,
            task_id=task.id,
            report_date=datetime.now(timezone.utc),
        )
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)

        # 3. 工程师更新日报
        token = create_test_token(engineer.id)
        response = await client.put(
            f"/v1/daily-reports/{report.id}",
            json={
                "today_hours": 10.0,
                "current_stage": "testing",
                "summary": "转入测试阶段",
            },
            headers=get_auth_headers(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["today_hours"] == 10.0
        assert data["current_stage"] == "testing"

    @pytest.mark.asyncio
    async def test_delete_daily_report_admin_only(
        self, db_session: AsyncSession, client: AsyncClient
    ):
        """
        测试管理员删除日报
        - 只有管理员可以删除
        """
        # 1. 创建 PM、工程师和管理员
        pm = await create_test_user(
            db_session,
            email="pm_delete@example.com",
            is_superuser=False,
        )
        pm.role = UserRoleType.PM
        db_session.add(pm)
        await db_session.commit()

        engineer = await create_test_user(
            db_session,
            email="eng_delete@example.com",
            is_superuser=False,
        )
        engineer.role = UserRoleType.ENGINEER
        db_session.add(engineer)
        await db_session.commit()

        admin = await create_test_user(
            db_session,
            email="admin_delete@example.com",
            is_superuser=True,
        )

        # 2. 创建任务和日报
        task = await create_test_task(db_session, pm, engineer)

        report = DailyReport(
            today_hours=8.0,
            current_stage=ReportStage.DEVELOPING,
            engineer_id=engineer.id,
            task_id=task.id,
            report_date=datetime.now(timezone.utc),
        )
        db_session.add(report)
        await db_session.commit()
        await db_session.refresh(report)

        # 3. 管理员删除日报
        token = create_test_token(admin.id)
        response = await client.delete(
            f"/v1/daily-reports/{report.id}",
            headers=get_auth_headers(token),
        )
        assert response.status_code == 200

        # 4. 验证已删除
        deleted_report = await db_session.get(DailyReport, report.id)
        assert deleted_report is None