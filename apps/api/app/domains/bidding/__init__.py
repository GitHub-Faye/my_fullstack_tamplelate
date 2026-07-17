"""
Bidding 模块

竞价结算相关功能。
"""

from app.domains.bidding.router import router as bidding_router

__all__ = ["bidding_router"]