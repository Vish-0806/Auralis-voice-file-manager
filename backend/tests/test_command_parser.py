from ai_engine.command_parser import parse_command
from ai_engine.entity_extractor import extract_file_names, extract_folder_names, extract_targets
from ai_engine.intent_classifier import classify_intent


def assert_parsed(cmd, action, target):
    res = parse_command(cmd)
    assert res["action"] == action, f"action mismatch for '{cmd}': {res}"
    assert res["target"] == target, f"target mismatch for '{cmd}': {res}"


def test_open_variations():
    variants = [
        "open downloads",
        "open download",
        "open my downloads",
        "open my downloads folder",
        "please open downloads",
        "can you open downloads",
        "could you open my downloads",
    ]

    for v in variants:
        assert_parsed(v, "open", "downloads")


def test_create_folder_variations():
    assert_parsed("create folder test", "create_folder", "test")
    assert_parsed("please create folder projects", "create_folder", "projects")


def test_delete_variations():
    assert_parsed("delete document", "delete", "documents")
    assert_parsed("remove pictures", "delete", "pictures")


def test_unknown():
    res = parse_command("fly to the moon")
    assert res["action"] == "unknown"


def test_intent_classifier_variations():
    assert classify_intent("open downloads") == "open"
    assert classify_intent("create folder notes") == "create_folder"
    assert classify_intent("delete document") == "delete"
    assert classify_intent("move downloads to archive") == "move"
    assert classify_intent("rename report.txt to summary.txt") == "rename"
    assert classify_intent("search for receipts") == "search"
    assert classify_intent("sing a song") == "unknown"


def test_entity_extractor_helpers():
    assert extract_file_names('open "report.txt"') == ["report.txt"]
    assert extract_folder_names("open my downloads folder") == ["downloads"]
    assert extract_targets("open my downloads folder", intent="open") == "downloads"
    assert extract_targets("search for receipts", intent="search") == "receipts"
