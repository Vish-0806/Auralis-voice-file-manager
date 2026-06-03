from ai_engine.command_parser import parse_command


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
