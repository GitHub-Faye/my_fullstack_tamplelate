from app.domains.user.router.user import router as user_router
from app.domains.user.router.login import router as login_router

__all__ = ["user_router", "login_router"]
