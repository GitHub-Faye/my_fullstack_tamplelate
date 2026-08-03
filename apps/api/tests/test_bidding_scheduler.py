"""
竞价自动结算调度 — 测试

验证：
- 过截止时间、有人报价 → 自动结算选中标人
- 过截止时间、无人报价 → 自动重新发布（重置倒计时），保持 BIDDING 状态
- 未过截止时间 → 不做任何处理
"""
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.core.models import Task, TaskStatus, TaskType, User, UserRoleType, Bid
import app.tasks.bidding_scheduler as scheduler_mod


async def create_user(session, role, email):
    user = User(email=email, hashed_password="x", role=role, is_active=True)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_task(session, pm, status=TaskStatus.BIDDING, deadline=None) -> Task:
    task = Task(
        name=f"Task {uuid.uuid4().hex[:8]}",
        status=status,
        pm_id=pm.id,
        task_type=TaskType.NORMAL,
        bidding_deadline=deadline,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@pytest.fixture(autouse=True)
def _patch_scheduler_session_factory(engine, monkeypatch):
    """让调度器使用和测试用例相同的内存数据库"""
    test_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    monkeypatch.setattr(scheduler_mod, "AsyncSessionLocal", test_session_factory)


class TestBiddingScheduler:
    @pytest.mark.asyncio
    async def test_overdue_with_bids_settles_winner(self, db_session):
        """过截止 + 有人报价 → 自动结算，选中标人"""
        pm = await create_user(db_session, UserRoleType.PM, f"pm_{uuid.uuid4().hex[:6]}@t.com")
        e1 = await create_user(db_session, UserRoleType.ENGINEER, f"e1_{uuid.uuid4().hex[:6]}@t.com")
        e2 = await create_user(db_session, UserRoleType.ENGINEER, f"e2_{uuid.uuid4().hex[:6]}@t.com")

        deadline = datetime.now() - timedelta(hours=1)  # naive local time
        task = await create_task(db_session, pm, deadline=deadline)
        db_session.add(Bid(task_id=task.id, engineer_id=e1.id, T_reported=8.0, amount=800.0))
        db_session.add(Bid(task_id=task.id, engineer_id=e2.id, T_reported=12.0, amount=1200.0))
        await db_session.commit()

        await scheduler_mod.settle_overdue_bidding_tasks()

        # 调度器内部使用自己的 session 并 commit，所以需要重新查询
        new_session_factory = async_sessionmaker(
            db_session.bind,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with new_session_factory() as new_session:
            updated = await new_session.get(Task, task.id)
            assert updated.status == TaskStatus.PENDING_START

    @pytest.mark.asyncio
    async def test_overdue_no_bids_republishes(self, db_session):
        """过截止 + 无人报价 → 自动重新发布，状态保持 BIDDING 且 deadline 被重置为未来"""
        pm = await create_user(db_session, UserRoleType.PM, f"pm_{uuid.uuid4().hex[:6]}@t.com")
        past_deadline = datetime.now() - timedelta(hours=1)  # naive local time
        task = await create_task(db_session, pm, deadline=past_deadline)

        await scheduler_mod.settle_overdue_bidding_tasks()

        new_session_factory = async_sessionmaker(
            db_session.bind,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with new_session_factory() as new_session:
            updated = await new_session.get(Task, task.id)
            assert updated is not None
            # 无人报价时 repository.settle_bidding_task_async 将任务设为 UNCONFIRMED
            # 调度器的 _republish 再将其重置为 BIDDING + 新 deadline
            assert updated.status == TaskStatus.BIDDING, f"Expected BIDDING, got {updated.status}"
            assert updated.bidding_deadline is not None
            # deadline 现在是 naive local 时间，直接比较
            assert updated.bidding_deadline > datetime.now()

    @pytest.mark.asyncio
    async def test_not_yet_deadline_left_untouched(self, db_session):
        """未过截止时间 → 不处理"""
        pm = await create_user(db_session, UserRoleType.PM, f"pm_{uuid.uuid4().hex[:6]}@t.com")
        future_deadline = datetime.now() + timedelta(hours=1)  # naive local time
        task = await create_task(db_session, pm, deadline=future_deadline)

        await scheduler_mod.settle_overdue_bidding_tasks()

        new_session_factory = async_sessionmaker(
            db_session.bind,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with new_session_factory() as new_session:
            updated = await new_session.get(Task, task.id)
            assert updated is not None
            assert updated.status == TaskStatus.BIDDING
            assert updated.bidding_deadline is not None
            # naive local 时间直接比较
            assert updated.bidding_deadline > datetime.now()
