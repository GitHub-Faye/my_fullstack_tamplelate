"""
竞价结算任务测试模块

测试竞价结算的完整流程：
- 中标人计算
- 边界情况处理
- 任务状态更新
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.models import Task, TaskStatus, Bid, User, UserRoleType
from app.tasks.bidding_tasks import settle_bidding_task_async


async def create_test_task(
    session: AsyncSession,
    pm: User,
    status: TaskStatus = TaskStatus.BIDDING,
    bidding_deadline: datetime | None = None
) -> Task:
    """创建测试任务"""
    task = Task(
        name="Test Task for Bidding",
        description="Test task description",
        status=status,
        pm_id=pm.id,
        task_type="normal",
        bidding_deadline=bidding_deadline
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def create_test_user(
    session: AsyncSession,
    role: UserRoleType = UserRoleType.ENGINEER,
    email: str | None = None
) -> User:
    """创建测试用户"""
    if email is None:
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"

    user = User(
        email=email,
        hashed_password="hashed_password",
        role=role,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_test_bid(
    session: AsyncSession,
    task: Task,
    engineer: User,
    T_reported: float,
    amount: float
) -> Bid:
    """创建测试报价"""
    bid = Bid(
        task_id=task.id,
        engineer_id=engineer.id,
        T_reported=T_reported,
        amount=amount
    )
    session.add(bid)
    await session.commit()
    await session.refresh(bid)
    return bid


class TestBiddingSettlement:
    """竞价结算测试类"""

    @pytest.mark.asyncio
    async def test_settle_bidding_task_success(self, db_session: AsyncSession):
        """
        测试正常竞价结算流程
        - 3个工程师报价
        - 自动选择最接近平均价的工程师中标
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(db_session, UserRoleType.PM, "pm1@test.com")
        engineer1 = await create_test_user(db_session, UserRoleType.ENGINEER, "eng1@test.com")
        engineer2 = await create_test_user(db_session, UserRoleType.ENGINEER, "eng2@test.com")
        engineer3 = await create_test_user(db_session, UserRoleType.ENGINEER, "eng3@test.com")

        # 2. 创建竞价任务（已过截止时间）
        deadline = datetime.now() - timedelta(hours=1)
        task = await create_test_task(
            db_session,
            pm,
            status=TaskStatus.BIDDING,
            bidding_deadline=deadline
        )

        # 3. 工程师报价
        # amount = H0 * T_reported (假设 H0=100)
        # engineer1: 800 (T_reported=8.0)
        # engineer2: 1000 (T_reported=10.0)
        # engineer3: 1200 (T_reported=12.0)
        # 平均值 = 1000，engineer2 最接近
        await create_test_bid(db_session, task, engineer1, 8.0, 800.0)
        await create_test_bid(db_session, task, engineer2, 10.0, 1000.0)
        await create_test_bid(db_session, task, engineer3, 12.0, 1200.0)

        # 4. 执行结算任务
        result = await settle_bidding_task_async(db_session, str(task.id))

        # 5. 验证结果
        assert result["status"] == "success"
        assert result["bid_count"] == 3
        assert result["avg_amount"] == 1000.0
        assert result["winner_id"] == str(engineer2.id)
        assert result["winner_amount"] == 1000.0

        # 6. 验证任务状态更新
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.status == TaskStatus.PENDING_START
        assert updated_task.engineer_id == engineer2.id

    @pytest.mark.asyncio
    async def test_settle_bidding_task_no_bids(self, db_session: AsyncSession):
        """
        测试无人报价情况
        - 任务应回退到 UNCONFIRMED 状态
        """
        # 1. 创建 PM
        pm = await create_test_user(db_session, UserRoleType.PM, "pm2@test.com")

        # 2. 创建竞价任务（已过截止时间）
        deadline = datetime.now() - timedelta(hours=1)
        task = await create_test_task(
            db_session,
            pm,
            status=TaskStatus.BIDDING,
            bidding_deadline=deadline
        )

        # 3. 执行结算（无报价）
        result = await settle_bidding_task_async(db_session, str(task.id))

        # 4. 验证结果
        assert result["status"] == "no_bids"
        assert result["bid_count"] == 0
        assert result["winner_id"] is None

        # 5. 验证任务状态
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.status == TaskStatus.UNCONFIRMED
        assert updated_task.engineer_id is None

    @pytest.mark.asyncio
    async def test_settle_bidding_task_single_bid(self, db_session: AsyncSession):
        """
        测试仅一人报价情况
        - 该工程师自动中标
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(db_session, UserRoleType.PM, "pm3@test.com")
        engineer = await create_test_user(db_session, UserRoleType.ENGINEER, "eng4@test.com")

        # 2. 创建竞价任务（已过截止时间）
        deadline = datetime.now() - timedelta(hours=1)
        task = await create_test_task(
            db_session,
            pm,
            status=TaskStatus.BIDDING,
            bidding_deadline=deadline
        )

        # 3. 仅一个工程师报价
        await create_test_bid(db_session, task, engineer, 10.0, 1000.0)

        # 4. 执行结算
        result = await settle_bidding_task_async(db_session, str(task.id))

        # 5. 验证结果
        assert result["status"] == "success"
        assert result["bid_count"] == 1
        assert result["winner_id"] == str(engineer.id)

        # 6. 验证任务状态
        updated_task = await db_session.get(Task, task.id)
        assert updated_task.status == TaskStatus.PENDING_START
        assert updated_task.engineer_id == engineer.id

    @pytest.mark.asyncio
    async def test_settle_bidding_task_not_in_bidding_status(self, db_session: AsyncSession):
        """
        测试任务不在竞价状态
        - 应返回错误状态
        """
        # 1. 创建 PM
        pm = await create_test_user(db_session, UserRoleType.PM, "pm4@test.com")

        # 2. 创建非竞价状态任务
        task = await create_test_task(
            db_session,
            pm,
            status=TaskStatus.IN_PROGRESS
        )

        # 3. 执行结算
        result = await settle_bidding_task_async(db_session, str(task.id))

        # 4. 验证结果
        assert "invalid_status" in result["status"]
        assert result["bid_count"] == 0

    @pytest.mark.asyncio
    async def test_settle_bidding_task_deadline_not_reached(self, db_session: AsyncSession):
        """
        测试截止时间未到
        - 应返回错误状态
        """
        # 1. 创建 PM
        pm = await create_test_user(db_session, UserRoleType.PM, "pm5@test.com")

        # 2. 创建竞价任务（截止时间未到）
        deadline = datetime.now() + timedelta(hours=1)
        task = await create_test_task(
            db_session,
            pm,
            status=TaskStatus.BIDDING,
            bidding_deadline=deadline
        )

        # 3. 执行结算
        result = await settle_bidding_task_async(db_session, str(task.id))

        # 4. 验证结果
        assert result["status"] == "deadline_not_reached"

    @pytest.mark.asyncio
    async def test_settle_bidding_task_winner_selection(self, db_session: AsyncSession):
        """
        测试中标人选择逻辑
        - 4个工程师报价，验证选择最接近平均值的
        """
        # 1. 创建 PM 和工程师
        pm = await create_test_user(db_session, UserRoleType.PM, "pm6@test.com")
        engineers = [
            await create_test_user(db_session, UserRoleType.ENGINEER, f"eng{i}@test.com")
            for i in range(5, 9)
        ]

        # 2. 创建竞价任务
        deadline = datetime.now() - timedelta(hours=1)
        task = await create_test_task(
            db_session,
            pm,
            status=TaskStatus.BIDDING,
            bidding_deadline=deadline
        )

        # 3. 工程师报价
        # 平均值 = (500+800+1200+1500)/4 = 1000
        # engineer[1] (800) 差值 = 200
        # engineer[2] (1200) 差值 = 200
        # 选择第一个最接近的，即 engineer[1]
        await create_test_bid(db_session, task, engineers[0], 5.0, 500.0)
        await create_test_bid(db_session, task, engineers[1], 8.0, 800.0)
        await create_test_bid(db_session, task, engineers[2], 12.0, 1200.0)
        await create_test_bid(db_session, task, engineers[3], 15.0, 1500.0)

        # 4. 执行结算
        result = await settle_bidding_task_async(db_session, str(task.id))

        # 5. 验证结果
        assert result["status"] == "success"
        assert result["avg_amount"] == 1000.0
        # 验证选择的是 engineer[1] (第一个最接近的)
        assert result["winner_id"] == str(engineers[1].id)

    @pytest.mark.asyncio
    async def test_settle_bidding_task_task_not_found(self, db_session: AsyncSession):
        """
        测试任务不存在
        - 应返回 not_found 状态
        """
        # 执行结算（不存在的任务ID）
        fake_task_id = str(uuid.uuid4())
        result = await settle_bidding_task_async(db_session, fake_task_id)

        # 验证结果
        assert result["status"] == "not_found"