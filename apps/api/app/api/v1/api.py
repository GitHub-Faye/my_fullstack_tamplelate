from fastapi import APIRouter

from app.domains.user.router import router as user_router
from app.domains.item.router import router as item_router

router = APIRouter()

# 用户相关路由（登录 + 用户管理统一在 user.py 中定义）
# 路由路径已在 user.py 内以 /login/... 和 /users/... 区分，整体挂载一次即可
router.include_router(user_router, tags=["login", "users"])

# 物品相关路由
router.include_router(item_router, prefix="/items", tags=["items"])
