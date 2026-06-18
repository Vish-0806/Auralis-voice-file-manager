import time
from app.state_manager import StateManager


def test_state_manager_pending_action():
    # Make sure it starts clear
    StateManager.clear_pending_action()
    assert StateManager.get_pending_action() is None

    # Set pending action
    StateManager.set_pending_action(
        action="delete",
        target="report.pdf",
        destination="downloads"
    )

    pending = StateManager.get_pending_action()
    assert pending is not None
    assert pending["pending_action"] == "delete"
    assert pending["pending_target"] == "report.pdf"
    assert pending["pending_destination"] == "downloads"
    assert isinstance(pending["timestamp"], float)
    # Timestamp should be close to now
    assert time.time() - pending["timestamp"] < 5

    # Clear pending action
    StateManager.clear_pending_action()
    assert StateManager.get_pending_action() is None


def test_state_manager_multi_step_workflows():
    StateManager.clear_pending_action()
    assert StateManager.get_workflow_steps() == []

    # Add workflow steps
    step1 = {"step": 1, "description": "find target"}
    step2 = {"step": 2, "description": "request permission"}

    StateManager.add_workflow_step(step1)
    StateManager.add_workflow_step(step2)

    steps = StateManager.get_workflow_steps()
    assert len(steps) == 2
    assert steps[0] == step1
    assert steps[1] == step2

    # Clearing pending action should also clear steps
    StateManager.clear_pending_action()
    assert StateManager.get_workflow_steps() == []
