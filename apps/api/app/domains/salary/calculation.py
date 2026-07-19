"""
工资计算逻辑模块（兼容层）

提供工资试算功能。
此模块现为兼容层，核心逻辑已迁移至 service.py。

TODO: 逐步迁移 import 后删除此文件。
"""

from app.domains.salary.service import calculate_user_salary, calculate_all_salaries

__all__ = ["calculate_user_salary", "calculate_all_salaries"]
