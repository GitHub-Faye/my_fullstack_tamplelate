"""
审计日志模块 — 业务服务层（已弃用）

⚠️ 请直接使用 `app.domains.audit.repository.create_audit_log`。
此模块将在后续清理中移除。
"""

import warnings

warnings.warn(
    "service.py is deprecated — import create_audit_log from app.domains.audit.repository directly",
    DeprecationWarning,
    stacklevel=2,
)

from app.domains.audit.repository import create_audit_log  # noqa: F401