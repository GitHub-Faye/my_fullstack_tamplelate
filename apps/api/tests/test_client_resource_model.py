"""
ClientResource 和 SystemRule 模型测试

测试客资和系统规则模型的基本功能
"""

import pytest
from app.core.models import ClientResource, SystemRule, RuleCategory


def test_rule_category_enum_values():
    """测试规则分类枚举值"""
    assert RuleCategory.STARPOINT_REWARD == "starpoint_reward"
    assert RuleCategory.SALARY_FORMULA == "salary_formula"
    assert RuleCategory.CLIENT_RESOURCE == "client_resource"
    assert RuleCategory.COMPLETION_JUDGMENT == "completion_judgment"
    assert RuleCategory.SYSTEM_PARAM == "system_param"


def test_client_resource_model_fields():
    """测试客资模型字段"""
    resource = ClientResource(
        actual_count=120,
        baseline_count=100,
        pm_id="00000000-0000-0000-0000-000000000001",
        date="2026-07-17T00:00:00Z"
    )
    assert resource.actual_count == 120
    assert resource.baseline_count == 100


def test_system_rule_model_fields():
    """测试系统规则模型字段"""
    rule = SystemRule(
        category=RuleCategory.STARPOINT_REWARD,
        name="starpoint_base_value",
        value="1.0",
        is_public=True,
        is_active=True
    )
    assert rule.category == RuleCategory.STARPOINT_REWARD
    assert rule.name == "starpoint_base_value"
    assert rule.value == "1.0"
    assert rule.is_public is True
    assert rule.is_active is True


def test_system_rule_default_values():
    """测试系统规则默认值"""
    rule = SystemRule(
        category=RuleCategory.SYSTEM_PARAM,
        name="test_param",
        value="10"
    )
    assert rule.is_public is False
    assert rule.is_active is True


def test_client_resource_can_track_performance():
    """测试客资可以追踪绩效"""
    resource = ClientResource(
        actual_count=150,
        baseline_count=100,
        pm_id="00000000-0000-0000-0000-000000000001",
        date="2026-07-17T00:00:00Z"
    )
    # 计算超额完成率
    performance_rate = (resource.actual_count - resource.baseline_count) / resource.baseline_count
    assert performance_rate == 0.5  # 超额完成 50%
