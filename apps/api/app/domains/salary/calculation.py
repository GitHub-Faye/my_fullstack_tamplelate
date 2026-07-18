"""
工资计算逻辑模块

提供工资试算功能：
- 工程师工资：S下 = (S0 - P差额) × K
- PM 工资：S总 = S底 + S考
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import User, UserRoleType
from app.domains.salary import repository as salary_repo
from app.domains.starpoint import repository as starpoint_repo


async def calculate_user_salary(
    *,
    session: AsyncSession,
    user: User,
) -> dict:
    """
    计算用户工资（工程师或 PM）

    Args:
        session: 数据库会话
        user: 用户对象

    Returns:
        工资计算详情字典

    Raises:
        ValueError: 用户角色不支持工资计算
    """
    if user.role == UserRoleType.ENGINEER:
        # 获取 K 系数
        k_coefficient = await starpoint_repo.calculate_k_coefficient(
            session=session,
            engineer_id=user.id,
        )
        return await salary_repo.calculate_engineer_salary(
            session=session,
            engineer=user,
            k_coefficient=k_coefficient,
        )
    elif user.role == UserRoleType.PM:
        return await salary_repo.calculate_pm_salary(pm=user)
    else:
        raise ValueError(f"User role {user.role} does not support salary calculation")
