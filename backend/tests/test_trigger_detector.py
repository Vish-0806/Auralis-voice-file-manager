# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone
from memory.recommendations import (
    TriggerEvent,
    TriggerCondition,
    TriggerEvaluation,
    TriggerDetector,
)


def test_workspace_trigger():
    detector = TriggerDetector()
    event = TriggerEvent(event_type="WorkspaceOpened", value="C:/Projects/Auralis")
    condition = TriggerCondition(trigger_type="WorkspaceOpened", expected_value="c:/projects/auralis", match_mode="exact")
    
    eval_res = detector.evaluate(event, condition)
    assert eval_res.triggered is True
    assert eval_res.matched_event == event

    # Fails match
    condition_fail = TriggerCondition(trigger_type="WorkspaceOpened", expected_value="c:/projects/other", match_mode="exact")
    assert detector.evaluate(event, condition_fail).triggered is False


def test_application_trigger():
    detector = TriggerDetector()
    event = TriggerEvent(event_type="ApplicationOpened", value="Google Chrome")
    condition = TriggerCondition(trigger_type="ApplicationOpened", expected_value="Chrome", match_mode="contains")
    
    eval_res = detector.evaluate(event, condition)
    assert eval_res.triggered is True
    assert eval_res.matched_event == event


def test_time_and_day_trigger():
    detector = TriggerDetector()
    event_time = TriggerEvent(event_type="TimeOfDay", value="09:00")
    cond_time = TriggerCondition(trigger_type="TimeOfDay", expected_value="09:00", match_mode="exact")
    assert detector.evaluate(event_time, cond_time).triggered is True

    event_day = TriggerEvent(event_type="DayOfWeek", value="Monday")
    cond_day = TriggerCondition(trigger_type="DayOfWeek", expected_value="monday", match_mode="exact")
    assert detector.evaluate(event_day, cond_day).triggered is True


def test_multiple_trigger_evaluation():
    detector = TriggerDetector()
    events = [
        TriggerEvent(event_type="WorkspaceOpened", value="c:/projects"),
        TriggerEvent(event_type="ApplicationOpened", value="Edge")
    ]
    
    # Active conditions
    cond1 = TriggerCondition(trigger_type="WorkspaceOpened", expected_value="c:/projects")
    cond2 = TriggerCondition(trigger_type="ApplicationOpened", expected_value="Edge")
    
    # Verify we can iterate and match
    matched = []
    for e in events:
        for c in [cond1, cond2]:
            res = detector.evaluate(e, c)
            if res.triggered:
                matched.append(e)
                
    assert len(matched) == 2


def test_invalid_trigger_handling():
    detector = TriggerDetector()
    event = TriggerEvent(event_type="WorkspaceOpened", value="c:/projects")
    
    # Mismatched trigger type
    cond_mismatched = TriggerCondition(trigger_type="ApplicationOpened", expected_value="Chrome")
    assert detector.evaluate(event, cond_mismatched).triggered is False
