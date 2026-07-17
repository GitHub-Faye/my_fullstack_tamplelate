from fastapi import APIRouter

from app.domains.user.router import login_router, user_router
from app.domains.item.router import router as item_router
from app.domains.task.router import router as task_router
from app.domains.task.router_admin import router as task_admin_router
from app.domains.bid.router import router as bid_router

router = APIRouter()

# 用户相关路由
router.include_router(login_router, tags=["login"])
router.include_router(user_router, prefix="/users", tags=["users"])

# 物品相关路由
router.include_router(item_router, prefix="/items", tags=["items"])

# 任务相关路由
router.include_router(task_router, prefix="/tasks", tags=["tasks"])
router.include_router(task_admin_router, prefix="/tasks", tags=["tasks-admin"])

# 竞价相关路由
router.include_router(bid_router, tags=["bids"])
