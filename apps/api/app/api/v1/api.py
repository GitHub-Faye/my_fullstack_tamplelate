from fastapi import APIRouter

from app.domains.role.router import router as role_router
from app.domains.user.router import router as user_router

router = APIRouter()


# 系统级端点（不属于任何业务域）
@router.get("/health-check", tags=["system"])
async def health_check() -> bool:
    """健康检查端点，返回 True 表示服务正常运行。"""
    return True


# 用户相关路由（登录 + 用户管理统一在 user.py 中定义）
# 路由路径已在 user.py 内以 /login/... 和 /users/... 区分，整体挂载一次即可
router.include_router(user_router, tags=["login", "users"])

# 角色相关路由
router.include_router(role_router, prefix="/roles", tags=["roles"])
