"""Unit tests for RecurringTriggerValidator, RecurringScheduleCalculator, and BackgroundJobScheduler integration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict

from brain.execution.background_job_scheduler import (
    BackgroundJobPriority,
    BackgroundJobScheduler,
    BackgroundJobStatus,
    BackgroundJobTriggerType,
    RecurringScheduleCalculator,
    RecurringTriggerValidator,
    TriggerValidationResult,
    calculate_next_run,
)


def test_once_trigger_calculation() -> None:
    """Verifies ONCE trigger calculation with delay_seconds and run_at."""
    calculator = RecurringScheduleCalculator()
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)

    # Delay seconds
    next_run = calculator.calculate_next_run(
        BackgroundJobTriggerType.ONCE,
        parameters={"delay_seconds": 120},
        from_time=now,
    )
    assert next_run == datetime(2026, 7, 28, 12, 2, 0, tzinfo=timezone.utc)

    # Specific ISO run_at
    target_iso = "2026-08-01T15:30:00+00:00"
    next_run_iso = calculator.calculate_next_run(
        BackgroundJobTriggerType.ONCE,
        parameters={"run_at": target_iso},
        from_time=now,
    )
    assert next_run_iso == datetime(2026, 8, 1, 15, 30, 0, tzinfo=timezone.utc)

    # Completed job returning None
    finished_run = calculator.calculate_next_run(
        BackgroundJobTriggerType.ONCE,
        parameters={"delay_seconds": 60},
        from_time=now,
        last_run=now,
    )
    assert finished_run is None


def test_interval_trigger_calculation() -> None:
    """Verifies INTERVAL trigger advances timestamp deterministically."""
    calculator = RecurringScheduleCalculator()
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)

    next_run = calculator.calculate_next_run(
        BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 300},
        from_time=now,
    )
    assert next_run == datetime(2026, 7, 28, 12, 5, 0, tzinfo=timezone.utc)

    # Calculation based on last_run
    last = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    current = datetime(2026, 7, 28, 12, 2, 0, tzinfo=timezone.utc)
    next_rescheduled = calculator.calculate_next_run(
        BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 300},
        from_time=current,
        last_run=last,
    )
    assert next_rescheduled == datetime(2026, 7, 28, 12, 5, 0, tzinfo=timezone.utc)


def test_daily_trigger_calculation() -> None:
    """Verifies DAILY trigger calculates next occurrence of HH:MM."""
    calculator = RecurringScheduleCalculator()
    now = datetime(2026, 7, 28, 10, 0, 0, tzinfo=timezone.utc)

    # Later today
    next_run = calculator.calculate_next_run(
        BackgroundJobTriggerType.DAILY,
        parameters={"time_of_day": "14:30"},
        from_time=now,
    )
    assert next_run == datetime(2026, 7, 28, 14, 30, 0, tzinfo=timezone.utc)

    # Tomorrow (time has passed today)
    next_tomorrow = calculator.calculate_next_run(
        BackgroundJobTriggerType.DAILY,
        parameters={"time_of_day": "08:15"},
        from_time=now,
    )
    assert next_tomorrow == datetime(2026, 7, 29, 8, 15, 0, tzinfo=timezone.utc)


def test_weekly_trigger_calculation() -> None:
    """Verifies WEEKLY trigger calculates next configured weekday and time."""
    calculator = RecurringScheduleCalculator()
    # 2026-07-28 is a Tuesday (weekday 1)
    now = datetime(2026, 7, 28, 10, 0, 0, tzinfo=timezone.utc)

    # Friday (weekday 4)
    next_fri = calculator.calculate_next_run(
        BackgroundJobTriggerType.WEEKLY,
        parameters={"day_of_week": 4, "time_of_day": "09:00"},
        from_time=now,
    )
    assert next_fri == datetime(2026, 7, 31, 9, 0, 0, tzinfo=timezone.utc)

    # Monday (weekday 0, next week)
    next_mon = calculator.calculate_next_run(
        BackgroundJobTriggerType.WEEKLY,
        parameters={"day_of_week": "Monday", "time_of_day": "11:00"},
        from_time=now,
    )
    assert next_mon == datetime(2026, 8, 3, 11, 0, 0, tzinfo=timezone.utc)


def test_monthly_trigger_calculation() -> None:
    """Verifies MONTHLY trigger calculates next configured month day."""
    calculator = RecurringScheduleCalculator()
    now = datetime(2026, 7, 10, 10, 0, 0, tzinfo=timezone.utc)

    # Later this month
    next_run = calculator.calculate_next_run(
        BackgroundJobTriggerType.MONTHLY,
        parameters={"day_of_month": 15, "time_of_day": "12:00"},
        from_time=now,
    )
    assert next_run == datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Next month (day has passed)
    next_month = calculator.calculate_next_run(
        BackgroundJobTriggerType.MONTHLY,
        parameters={"day_of_month": 5, "time_of_day": "08:00"},
        from_time=now,
    )
    assert next_month == datetime(2026, 8, 5, 8, 0, 0, tzinfo=timezone.utc)


def test_manual_trigger_calculation() -> None:
    """Verifies MANUAL trigger calculation always returns None."""
    calculator = RecurringScheduleCalculator()
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)

    assert calculator.calculate_next_run(BackgroundJobTriggerType.MANUAL, from_time=now) is None


def test_invalid_interval_validation() -> None:
    """Verifies validator rejects zero, negative, and non-numeric intervals."""
    validator = RecurringTriggerValidator()

    # Zero interval
    res_zero = validator.validate_trigger(BackgroundJobTriggerType.INTERVAL, {"interval_seconds": 0})
    assert res_zero.is_valid is False
    assert "greater than zero" in str(res_zero.error)

    # Negative interval
    res_neg = validator.validate_trigger(BackgroundJobTriggerType.INTERVAL, {"interval_seconds": -10})
    assert res_neg.is_valid is False

    # Non-numeric interval
    res_nan = validator.validate_trigger(BackgroundJobTriggerType.INTERVAL, {"interval_seconds": "invalid"})
    assert res_nan.is_valid is False

    # Missing interval
    res_missing = validator.validate_trigger(BackgroundJobTriggerType.INTERVAL, {})
    assert res_missing.is_valid is False


def test_invalid_weekday_validation() -> None:
    """Verifies validator rejects out-of-bounds weekday values and string names."""
    validator = RecurringTriggerValidator()

    # Negative day
    res_neg = validator.validate_trigger(BackgroundJobTriggerType.WEEKLY, {"day_of_week": -1})
    assert res_neg.is_valid is False

    # Out of bounds day
    res_oob = validator.validate_trigger(BackgroundJobTriggerType.WEEKLY, {"day_of_week": 7})
    assert res_oob.is_valid is False

    # Invalid weekday string name
    res_str = validator.validate_trigger(BackgroundJobTriggerType.WEEKLY, {"day_of_week": "Funday"})
    assert res_str.is_valid is False


def test_invalid_month_day_validation() -> None:
    """Verifies validator rejects invalid month days (< 1 or > 31)."""
    validator = RecurringTriggerValidator()

    res_zero = validator.validate_trigger(BackgroundJobTriggerType.MONTHLY, {"day_of_month": 0})
    assert res_zero.is_valid is False

    res_oob = validator.validate_trigger(BackgroundJobTriggerType.MONTHLY, {"day_of_month": 32})
    assert res_oob.is_valid is False


def test_invalid_time_format_validation() -> None:
    """Verifies validator rejects malformed time_of_day strings."""
    validator = RecurringTriggerValidator()

    res_hour = validator.validate_trigger(BackgroundJobTriggerType.DAILY, {"time_of_day": "25:00"})
    assert res_hour.is_valid is False

    res_min = validator.validate_trigger(BackgroundJobTriggerType.DAILY, {"time_of_day": "12:60"})
    assert res_min.is_valid is False

    res_fmt = validator.validate_trigger(BackgroundJobTriggerType.DAILY, {"time_of_day": "12-00"})
    assert res_fmt.is_valid is False


def test_leap_year_handling() -> None:
    """Verifies MONTHLY schedule safely handles Feb 29 on leap year vs non-leap year."""
    calculator = RecurringScheduleCalculator()

    # 2028 is a leap year -> Feb 29 exists
    ref_leap = datetime(2028, 2, 1, 10, 0, 0, tzinfo=timezone.utc)
    next_leap = calculator.calculate_next_run(
        BackgroundJobTriggerType.MONTHLY,
        parameters={"day_of_month": 29, "time_of_day": "12:00"},
        from_time=ref_leap,
    )
    assert next_leap == datetime(2028, 2, 29, 12, 0, 0, tzinfo=timezone.utc)

    # 2027 is non-leap -> Feb 31/29 clamps to Feb 28
    ref_non_leap = datetime(2027, 2, 1, 10, 0, 0, tzinfo=timezone.utc)
    next_non_leap = calculator.calculate_next_run(
        BackgroundJobTriggerType.MONTHLY,
        parameters={"day_of_month": 31, "time_of_day": "12:00"},
        from_time=ref_non_leap,
    )
    assert next_non_leap == datetime(2027, 2, 28, 12, 0, 0, tzinfo=timezone.utc)


def test_month_length_handling() -> None:
    """Verifies MONTHLY schedule clamps day 31 on 30-day months (April 31 -> April 30)."""
    calculator = RecurringScheduleCalculator()
    ref_april = datetime(2026, 4, 1, 10, 0, 0, tzinfo=timezone.utc)

    next_april = calculator.calculate_next_run(
        BackgroundJobTriggerType.MONTHLY,
        parameters={"day_of_month": 31, "time_of_day": "10:00"},
        from_time=ref_april,
    )
    # April has 30 days -> day 31 clamps to April 30
    assert next_april == datetime(2026, 4, 30, 10, 0, 0, tzinfo=timezone.utc)


def test_recurring_calculator_standalone() -> None:
    """Verifies RecurringScheduleCalculator can be instantiated and used independently."""
    calculator = RecurringScheduleCalculator()
    now = datetime.now(timezone.utc)

    result = calculator.calculate_next_run(
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 60},
        from_time=now,
    )
    assert result is not None
    assert result > now


def test_recurring_validator_standalone() -> None:
    """Verifies RecurringTriggerValidator can be instantiated and used independently."""
    validator = RecurringTriggerValidator()

    res = validator.validate_trigger(
        trigger_type=BackgroundJobTriggerType.DAILY,
        parameters={"time_of_day": "09:30"},
    )
    assert isinstance(res, TriggerValidationResult)
    assert res.is_valid is True


def test_scheduler_integration_valid_job() -> None:
    """Verifies BackgroundJobScheduler validates and schedules valid jobs."""
    scheduler = BackgroundJobScheduler()

    job = scheduler.create_job(
        name="Valid Daily Sync",
        trigger_type=BackgroundJobTriggerType.DAILY,
        parameters={"time_of_day": "03:00"},
    )
    assert job is not None
    assert job.next_run is not None


def test_scheduler_integration_invalid_job() -> None:
    """Verifies BackgroundJobScheduler rejects job creation with invalid trigger parameters."""
    scheduler = BackgroundJobScheduler()

    job = scheduler.create_job(
        name="Invalid Interval Job",
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": -50},
    )
    assert job is None


def test_scheduler_integration_update_validation() -> None:
    """Verifies BackgroundJobScheduler.update_job rejects invalid trigger parameters."""
    scheduler = BackgroundJobScheduler()

    job = scheduler.create_job(
        name="Update Validation Test",
        trigger_type=BackgroundJobTriggerType.INTERVAL,
        parameters={"interval_seconds": 300},
    )
    assert job is not None

    # Reject invalid update
    assert scheduler.update_job(job.job_id, parameters={"interval_seconds": -5}) is False

    # Accept valid update
    assert scheduler.update_job(job.job_id, parameters={"interval_seconds": 600}) is True


def test_backward_compatibility() -> None:
    """Verifies module function calculate_next_run functions as expected."""
    now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    res = calculate_next_run(BackgroundJobTriggerType.INTERVAL, {"interval_seconds": 120}, from_time=now)

    assert res == datetime(2026, 7, 28, 12, 2, 0, tzinfo=timezone.utc)
