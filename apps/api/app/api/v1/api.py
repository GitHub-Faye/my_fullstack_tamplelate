from fastapi import APIRouter

from app.domains.user.router import login_router, user_router, admin_router
from app.domains.item.router import router as item_router
from app.domains.task.router import router as task_router
from app.domains.bidding.router import router as bidding_router
from app.domains.daily_report.router import router as daily_report_router
from app.domains.starpoint.router import router as starpoint_router
from app.domains.salary.router import router as salary_router
from app.domains.dashboard.router import router as dashboard_router
from app.domains.system_rule.router import router as system_rule_router
from app.domains.client_resource.router import router as client_resource_router
from app.domains.role.router import router as role_router
from app.domains.audit.router import router as audit_router

router = APIRouter()

# 用户相关路由
router.include_router(login_router, tags=["login"])
router.include_router(user_router, prefix="/users", tags=["users"])
router.include_router(admin_router, prefix="/admin", tags=["admin-users"])

# # 物品相关路由
# router.include_router(item_router, prefix="/items", tags=["items"])

# 任务相关路由（统一 router，包含 PM CRUD + 管理员操作 + 工程师执行）
router.include_router(task_router, prefix="/tasks", tags=["tasks"])

# 竞价相关路由（报价 + 结算）
router.include_router(bidding_router, tags=["bidding"])

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

# 客资管理相关路由
router.include_router(client_resource_router, prefix="/client-resources", tags=["client-resources"])

# 审计日志相关路由
router.include_router(role_router, prefix="/admin", tags=["admin-roles"])
router.include_router(audit_router, prefix="/audit-logs", tags=["audit-logs"])
