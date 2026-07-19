"""
竞价模块

提供竞价报价、结算和发布到竞价池的完整功能。
"""
from app.domains.bidding.router import router

__all__ = ["router"]