"""
DailyReport 和 StarPointRecord 模型测试

测试日报和星点记录模型的基本功能
"""

import pytest
from app.core.models import DailyReport, StarPointRecord, ReportStage, JudgmentType


def test_report_stage_enum_values():
    """测试日报阶段枚举值"""
    assert ReportStage.DEVELOPING == "developing"
    assert ReportStage.TESTING == "testing"
    assert ReportStage.COMPLETED == "completed"
    assert ReportStage.PAUSED == "paused"


def test_judgment_type_enum_values():
    """测试星点判定类型枚举值"""
    assert JudgmentType.MANUAL == "manual"
    assert JudgmentType.AUTO_RATIO == "auto_ratio"
    assert JudgmentType.AUTO_THRESHOLD == "auto_threshold"


def test_daily_report_model_fields():
    """测试日报模型字段"""
    report = DailyReport(
        today_hours=8.0,
        current_stage=ReportStage.DEVELOPING,
        engineer_id="00000000-0000-0000-0000-000000000001",
        task_id="00000000-0000-0000-0000-000000000002",
        report_date="2026-07-17T00:00:00Z"
    )
    assert report.today_hours == 8.0
    assert report.current_stage == ReportStage.DEVELOPING
    assert report.has_blocker is False
    assert report.starpoint_change == 0


def test_starpoint_record_model_fields():
    """测试星点记录模型字段"""
    record = StarPointRecord(
        change_amount=5,
        judgment_type=JudgmentType.AUTO_RATIO,
        engineer_id="00000000-0000-0000-0000-000000000001",
        T_reported=8.0,
        T_actual=7.5
    )
    assert record.change_amount == 5
    assert record.judgment_type == JudgmentType.AUTO_RATIO
    assert record.T_reported == 8.0
    assert record.T_actual == 7.5


def test_daily_report_can_change_stage():
    """测试日报阶段可以修改"""
    report = DailyReport(
        today_hours=8.0,
        current_stage=ReportStage.DEVELOPING,
        engineer_id="00000000-0000-0000-0000-000000000001",
        task_id="00000000-0000-0000-0000-000000000002",
        report_date="2026-07-17T00:00:00Z"
    )
    report.current_stage = ReportStage.TESTING
    assert report.current_stage == ReportStage.TESTING

    report.current_stage = ReportStage.COMPLETED
    assert report.current_stage == ReportStage.COMPLETED