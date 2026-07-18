"""
核心工具函数模块

提供跨模块复用的辅助函数。
"""

from app.core.dependencies import SessionDep
from app.core.models import User


async def get_engineer_H0(session: SessionDep, user_id) -> float:
    """
    获取工程师的基准时薪 H0。

    从数据库加载 User 记录，返回 H0 字段值；
    如果工程师不存在或未设置 H0，返回默认值 100.0。

    Args:
        session: 数据库会话
        user_id: 用户 ID

    Returns:
        float: 基准时薪
    """
    engineer = await session.get(User, user_id)
    return engineer.H0 if engineer and engineer.H0 else 100.0
