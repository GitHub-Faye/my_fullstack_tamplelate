from fastapi import APIRouter

from app.domains.user.router import login_router, user_router, admin_router
from app.domains.item.router import router as item_router
from app.domains.task.router import router as task_router
from app.domains.task.router_admin import router as task_admin_router
from app.domains.task.router_execution import router as task_execution_router
from app.domains.task.router_admin_execution import router as task_admin_execution_router
from app.domains.bid.router import router as bid_router
from app.domains.bidding.router import router as bidding_router
from app.domains.daily_report.router import router as daily_report_router
from app.domains.starpoint.router import router as starpoint_router
from app.domains.salary.router import router as salary_router
from app.domains.dashboard.router import router as dashboard_router
from app.domains.system_rule.router import router as system_rule_router

router = APIRouter()

# 用户相关路由
router.include_router(login_router, tags=["login"])
router.include_router(user_router, prefix="/users", tags=["users"])
router.include_router(admin_router, prefix="/admin", tags=["admin-users"])

# 物品相关路由
router.include_router(item_router, prefix="/items", tags=["items"])

# 任务相关路由
router.include_router(task_router, prefix="/tasks", tags=["tasks"])
router.include_router(task_admin_router, prefix="/tasks", tags=["tasks-admin"])
router.include_router(task_execution_router, prefix="/tasks", tags=["tasks-execution"])
router.include_router(task_admin_execution_router, prefix="/tasks", tags=["tasks-admin-execution"])

# 竞价相关路由
router.include_router(bid_router, tags=["bids"])

# 竞价结算相关路由
router.include_router(bidding_router, prefix="/tasks", tags=["bidding-settlement"])

# 日报相关路由
router.include_router(daily_report_router, prefix="/daily-reports", tags=["daily-reports"])

# 星点相关路由
router.include_router(starpoint_router, prefix="/starpoints", tags=["starpoints"])

# 工资相关路由
router.include_router(salary_router, prefix="/salaries", tags=["salaries"])

# Dashboard 相关路由
router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

# 规则配置相关路由
router.include_router(system_rule_router, prefix="/system-rules", tags=["system-rules"])
