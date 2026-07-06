import time
from app.confirmation_manager import ConfirmationManager


def test_confirmation_manager_pending_action():
    # Make sure it starts clear
    ConfirmationManager.clear_pending_action()
    assert ConfirmationManager.get_pending_action() is None

    # Set pending action
    ConfirmationManager.set_pending_action(
        action="delete",
        target="report.pdf",
        destination="downloads"
    )

    pending = ConfirmationManager.get_pending_action()
    assert pending is not None
    assert pending["pending_action"] == "delete"
    assert pending["pending_target"] == "report.pdf"
    assert pending["pending_destination"] == "downloads"
    assert isinstance(pending["timestamp"], float)
    # Timestamp should be close to now
    assert time.time() - pending["timestamp"] < 5

    # Clear pending action
    ConfirmationManager.clear_pending_action()
    assert ConfirmationManager.get_pending_action() is None


def test_confirmation_manager_multi_step_workflows():
    ConfirmationManager.clear_pending_action()
    assert ConfirmationManager.get_workflow_steps() == []

    # Add workflow steps
    step1 = {"step": 1, "description": "find target"}
    step2 = {"step": 2, "description": "request permission"}

    ConfirmationManager.add_workflow_step(step1)
    ConfirmationManager.add_workflow_step(step2)

    steps = ConfirmationManager.get_workflow_steps()
    assert len(steps) == 2
    assert steps[0] == step1
    assert steps[1] == step2

    # Clearing pending action should also clear steps
    ConfirmationManager.clear_pending_action()
    assert ConfirmationManager.get_workflow_steps() == []
