import pytest

from ai_engine.command_normalizer import normalize_command, normalize_target
from ai_engine.command_parser import parse_command
from ai_engine.entity_extractor import extract_file_names, extract_folder_names, extract_targets
from ai_engine.intent_classifier import classify_intent


@pytest.mark.parametrize(
    ("command", "expected_action", "expected_target"),
    [
        ("open downloads", "open", "downloads"),
        ("open download", "open", "downloads"),
        ("please open downloads", "open", "downloads"),
        ("open my downloads folder", "open", "downloads"),
        ("can you open documents", "open", "documents"),
        ("create folder college", "create_folder", "college"),
        ("create a folder called notes", "create_folder", "notes"),
        ("delete report.pdf", "delete", "report.pdf"),
        ("delete my report.pdf file", "delete", "report.pdf"),
    ],
)
def test_parse_command_cases(command, expected_action, expected_target):
    result = parse_command(command)

    assert result["action"] == expected_action
    assert result["target"] == expected_target


@pytest.mark.parametrize(
    ("command", "expected_intent"),
    [
        ("open downloads", "open"),
        ("create folder college", "create_folder"),
        ("delete report.pdf", "delete"),
        ("move downloads to archive", "move"),
        ("rename report.txt to summary.txt", "rename"),
        ("search for receipts", "search"),
        ("sing a song", "unknown"),
    ],
)
def test_intent_detection(command, expected_intent):
    assert classify_intent(command) == expected_intent


@pytest.mark.parametrize(
    ("command", "expected_target"),
    [
        ("open downloads", "downloads"),
        ("open download", "downloads"),
        ("please open downloads", "downloads"),
        ("open my downloads folder", "downloads"),
        ("can you open documents", "documents"),
        ("create folder college", "college"),
        ("create a folder called notes", "notes"),
        ("delete report.pdf", "report.pdf"),
        ("delete my report.pdf file", "report.pdf"),
    ],
)
def test_target_extraction(command, expected_target):
    intent = classify_intent(command)
    assert extract_targets(command, intent=intent) == expected_target


@pytest.mark.parametrize(
    ("raw_command", "expected_normalized"),
    [
        ("please open my downloads folder", "open downloads"),
        ("can you open the documents directory", "open documents"),
        ("could you delete my report.pdf file", "delete report.pdf"),
        ("please open download", "open downloads"),
        ("please open document", "open documents"),
        ("please open picture", "open pictures"),
        ("please open video", "open videos"),
    ],
)
def test_command_normalization(raw_command, expected_normalized):
    assert normalize_command(raw_command) == expected_normalized


@pytest.mark.parametrize(
    ("target", "expected_normalized"),
    [
        ("download", "downloads"),
        ("document", "documents"),
        ("picture", "pictures"),
        ("video", "videos"),
        ("downloads", "downloads"),
    ],
)
def test_target_normalization(target, expected_normalized):
    assert normalize_target(target) == expected_normalized


def test_entity_extractor_helpers():
    assert extract_file_names('open "report.txt"') == ["report.txt"]
    assert extract_folder_names("open my downloads folder") == ["downloads"]
    assert extract_targets("search for receipts", intent="search") == "receipts"


def test_unknown_command_behaviour():
    result = parse_command("fly to the moon")

    assert result["action"] == "unknown"
    assert result["target"] == "fly to the moon"
