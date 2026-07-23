"""
Task 模型测试

测试任务、竞价、附件模型的基本功能
"""

import pytest
from app.core.models import Task, TaskStatus, TaskType, Bid, Attachment, User


def test_task_type_enum_values():
    """测试任务类型枚举值"""
    assert TaskType.NORMAL == "normal"
    assert TaskType.URGENT == "urgent"
    assert TaskType.CONVENIENT == "convenient"


def test_task_status_enum_values():
    """测试任务状态枚举值"""
    assert TaskStatus.UNCONFIRMED == "unconfirmed"
    assert TaskStatus.BIDDING == "bidding"
    assert TaskStatus.PENDING_START == "pending_start"
    assert TaskStatus.IN_PROGRESS == "in_progress"
    assert TaskStatus.PAUSED == "paused"
    assert TaskStatus.COMPLETED == "completed"


def test_task_default_values():
    """测试任务默认值"""
    task = Task(
        name="测试任务",
        pm_id="00000000-0000-0000-0000-000000000001"
    )
    assert task.task_type == TaskType.NORMAL
    assert task.status == TaskStatus.UNCONFIRMED
    assert task.T_reported is None
    assert task.T_actual is None
    assert task.engineer_id is None


def test_bid_model_fields():
    """测试竞价模型字段"""
    bid = Bid(
        T_reported=8.0,
        amount=800.0,
        task_id="00000000-0000-0000-0000-000000000001",
        engineer_id="00000000-0000-0000-0000-000000000002"
    )
    assert bid.T_reported == 8.0
    assert bid.amount == 800.0


def test_attachment_model_fields():
    """测试附件模型字段"""
    attachment = Attachment(
        file_name="test.pdf",
        file_path="/uploads/test.pdf",
        file_size=1024,
        task_id="00000000-0000-0000-0000-000000000001",
        uploaded_by="00000000-0000-0000-0000-000000000002"
    )
    assert attachment.file_name == "test.pdf"
    assert attachment.file_path == "/uploads/test.pdf"
    assert attachment.file_size == 1024


def test_task_can_change_status():
    """测试任务状态可以修改"""
    task = Task(
        name="测试任务",
        pm_id="00000000-0000-0000-0000-000000000001",
        status=TaskStatus.UNCONFIRMED
    )

    task.status = TaskStatus.BIDDING
    assert task.status == TaskStatus.BIDDING
