"""
系统规则 API 端点模块

提供规则配置相关的 RESTful API 端点：
- 查看规则列表
- 创建规则
- 更新规则
- 删除规则
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import (
    CurrentUser,
    SessionDep,
    require_scope,
)
from app.core.scopes import RuleScope
from app.core.schemas import Message
from app.core.errors import BusinessException, ErrorCode, raise_rule_not_found
from app.core.models import RuleCategory

from app.domains.system_rule import repository
from app.domains.system_rule.schemas import (
    SystemRuleCreate,
    SystemRuleUpdate,
    SystemRulePublic,
    SystemRulesPublic,
)


router = APIRouter()


# ==================== 管理员端点：规则配置 ====================


@router.get(
    "",
    response_model=SystemRulesPublic,
    summary="查看规则列表",
    description="管理员查看所有规则配置，支持按分类过滤",
)
async def read_rules(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    category: Annotated[str | None, Query(description="按分类过滤（starpoint_reward, completion_judgment, salary_formula, system_param）")] = None,
    page: Annotated[int, Query(ge=1, description="页码，从1开始")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量，默认20")] = 20,
    _: Annotated[None, Depends(require_scope(RuleScope.ADMIN))] = None,
) -> Any:
    """
    获取规则列表

    权限：管理员（需 rule:admin 权限）

    支持按分类过滤。
    """
    # 解析分类过滤
    category_filter = None
    if category:
        try:
            category_filter = RuleCategory(category)
        except ValueError:
            raise BusinessException(
                code=ErrorCode.SYSTEM_VALIDATION_ERROR,
                detail=f"Invalid category: {category}"
            )

    offset = (page - 1) * page_size

    rules, count = await repository.get_rules(
        session=session,
        category=category_filter,
        skip=offset,
        limit=page_size,
    )

    return SystemRulesPublic(
        data=[SystemRulePublic.model_validate(r) for r in rules],
        count=count,
        page=page,
        page_size=page_size,
        total_pages=(count + page_size - 1) // page_size if count > 0 else 0,
    )


@router.post(
    "",
    response_model=SystemRulePublic,
    summary="创建规则",
    description="管理员创建新规则配置",
)
async def create_rule(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    rule_in: SystemRuleCreate,
    _: Annotated[None, Depends(require_scope(RuleScope.ADMIN))] = None,
) -> Any:
    """
    创建规则

    权限：管理员（需 rule:admin 权限）

    支持的分类：
    - starpoint_reward: 星点奖励规则
    - completion_judgment: 完成判定规则
    - salary_formula: 工资计算公式
    - system_param: 系统参数
    """
    rule = await repository.create_rule(session=session, rule_in=rule_in)
    return rule


@router.get(
    "/{rule_id}",
    response_model=SystemRulePublic,
    summary="查看规则详情",
    description="管理员查看指定规则的详细信息",
)
async def read_rule(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    rule_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(RuleScope.ADMIN))] = None,
) -> Any:
    """
    获取规则详情

    权限：管理员（需 rule:admin 权限）
    """
    rule = await repository.get_rule(session=session, rule_id=rule_id)
    if not rule:
        raise_rule_not_found(detail=f"Rule with id {rule_id} not found")

    return rule


@router.put(
    "/{rule_id}",
    response_model=SystemRulePublic,
    summary="更新规则",
    description="管理员更新规则配置",
)
async def update_rule(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    rule_id: uuid.UUID,
    rule_in: SystemRuleUpdate,
    _: Annotated[None, Depends(require_scope(RuleScope.ADMIN))] = None,
) -> Any:
    """
    更新规则

    权限：管理员（需 rule:admin 权限）

    可更新字段：
    - category: 规则分类
    - name: 规则名称
    - applies_to: 适用对象
    - value: 规则值
    - is_public: 是否对员工公开
    - is_active: 是否启用
    """
    rule = await repository.get_rule(session=session, rule_id=rule_id)
    if not rule:
        raise_rule_not_found(detail=f"Rule with id {rule_id} not found")

    # 检查是否有更新字段
    if not rule_in.model_dump(exclude_none=True):
        raise BusinessException(
            code=ErrorCode.SYSTEM_VALIDATION_ERROR,
            detail="No fields provided for update"
        )

    updated_rule = await repository.update_rule(
        session=session,
        db_rule=rule,
        rule_in=rule_in,
    )
    return updated_rule


@router.delete(
    "/{rule_id}",
    response_model=Message,
    summary="删除规则",
    description="管理员删除规则配置",
)
async def delete_rule(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    rule_id: uuid.UUID,
    _: Annotated[None, Depends(require_scope(RuleScope.ADMIN))] = None,
) -> Message:
    """
    删除规则

    权限：管理员（需 rule:admin 权限）
    """
    rule = await repository.get_rule(session=session, rule_id=rule_id)
    if not rule:
        raise_rule_not_found(detail=f"Rule with id {rule_id} not found")

    await repository.delete_rule(session=session, db_rule=rule)
    return Message(message="Rule deleted successfully")