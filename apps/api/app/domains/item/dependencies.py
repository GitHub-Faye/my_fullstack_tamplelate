"""
"""

import uuid
from app.core.security import reusable_oauth2
from app.core.scopes import ItemScope
from app.core.errors import (
    raise_permission_denied,
)
from app.core.dependencies import (
    SessionDep,
    CurrentUser,
    get_user_scopes,
)


async def check_item_owner_or_admin(
    session: SessionDep,
    current_user: CurrentUser,
    item_owner_id: uuid.UUID,
) -> bool:
    """
    检查用户是否是 item 的所有者或拥有 admin 权限。
    
    参数：
    - session：数据库会话
    - current_user：当前用户
    - item_owner_id：item 的所有者 ID
    
    返回值：
    - bool：是否有权限
    
    异常：
    - 403 Forbidden：无权限
    """
    # 是自己的 item
    if item_owner_id == current_user.id:
        return True
    
    # 检查是否有 item:admin 权限
    user_scopes = await get_user_scopes(session, current_user)
    if ItemScope.ADMIN.value in user_scopes:
        return True
    
    raise_permission_denied("Not enough permissions")
