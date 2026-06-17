import os
import pytest
from unittest.mock import patch
from file_engine.transfer import copy_item, move_item


def test_invalid_parameters():
    # Test empty source/destination
    res1 = copy_item("", "dest")
    assert res1["status"] == "error"
    assert res1["error_class"] == "ValueError"

    res2 = move_item("src", "")
    assert res2["status"] == "error"
    assert res2["error_class"] == "ValueError"


def test_non_existent_source(tmp_path):
    non_existent = str(tmp_path / "does_not_exist.txt")
    dest = str(tmp_path / "dest")

    res_copy = copy_item(non_existent, dest)
    assert res_copy["status"] == "error"
    assert res_copy["error_class"] == "FileNotFoundError"

    res_move = move_item(non_existent, dest)
    assert res_move["status"] == "error"
    assert res_move["error_class"] == "FileNotFoundError"


def test_copy_file_success(tmp_path):
    # Create source file
    src_dir = tmp_path / "src_dir"
    src_dir.mkdir()
    src_file = src_dir / "test.txt"
    src_file.write_text("hello world")

    # Destination folder
    dest_dir = tmp_path / "dest_dir"

    # Copy item (dest_dir doesn't exist yet, should be created)
    res = copy_item(str(src_file), str(dest_dir))

    assert res["status"] == "success"
    assert "test.txt" in res["message"]
    assert os.path.exists(res["destination"])
    assert res["destination"] == str(dest_dir / "test.txt")
    with open(res["destination"], "r") as f:
        assert f.read() == "hello world"

    # Source should still exist
    assert src_file.exists()


def test_copy_directory_success(tmp_path):
    # Create source folder and file inside
    src_dir = tmp_path / "src_folder"
    src_dir.mkdir()
    sub_file = src_dir / "data.csv"
    sub_file.write_text("1,2,3")

    dest_dir = tmp_path / "dest_dir"

    res = copy_item(str(src_dir), str(dest_dir))

    assert res["status"] == "success"
    assert os.path.exists(res["destination"])
    assert os.path.isdir(res["destination"])
    
    copied_sub_file = os.path.join(res["destination"], "data.csv")
    assert os.path.exists(copied_sub_file)
    with open(copied_sub_file, "r") as f:
        assert f.read() == "1,2,3"

    assert src_dir.exists()


def test_move_file_success(tmp_path):
    src_dir = tmp_path / "src_dir"
    src_dir.mkdir()
    src_file = src_dir / "move_me.txt"
    src_file.write_text("moving text")

    dest_dir = tmp_path / "dest_dir"
    dest_dir.mkdir()

    res = move_item(str(src_file), str(dest_dir))

    assert res["status"] == "success"
    assert os.path.exists(res["destination"])
    # Source file should be gone
    assert not src_file.exists()
    
    with open(res["destination"], "r") as f:
        assert f.read() == "moving text"


def test_move_directory_success(tmp_path):
    src_dir = tmp_path / "src_folder"
    src_dir.mkdir()
    sub_file = src_dir / "content.txt"
    sub_file.write_text("content")

    dest_dir = tmp_path / "dest_dir"

    res = move_item(str(src_dir), str(dest_dir))

    assert res["status"] == "success"
    assert os.path.exists(res["destination"])
    assert not src_dir.exists()
    
    moved_sub_file = os.path.join(res["destination"], "content.txt")
    assert os.path.exists(moved_sub_file)


def test_duplicate_file_handling(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_file = src_dir / "report.pdf"
    src_file.write_text("pdf contents")

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    
    # Pre-create a file with the same name at destination
    existing_file = dest_dir / "report.pdf"
    existing_file.write_text("existing pdf")

    # Copy should suffix the new file to report_1.pdf
    res1 = copy_item(str(src_file), str(dest_dir))
    assert res1["status"] == "success"
    assert os.path.basename(res1["destination"]) == "report_1.pdf"

    # Pre-create report_1.pdf
    existing_file_2 = dest_dir / "report_1.pdf"
    existing_file_2.write_text("existing pdf 2")

    # Next copy should suffix to report_2.pdf
    res2 = copy_item(str(src_file), str(dest_dir))
    assert res2["status"] == "success"
    assert os.path.basename(res2["destination"]) == "report_2.pdf"


def test_duplicate_directory_handling(tmp_path):
    src_dir = tmp_path / "project"
    src_dir.mkdir()

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    
    # Pre-create directory
    (dest_dir / "project").mkdir()

    res1 = copy_item(str(src_dir), str(dest_dir))
    assert res1["status"] == "success"
    assert os.path.basename(res1["destination"]) == "project_1"


@patch("shutil.copy2")
def test_copy_permission_error(mock_copy, tmp_path):
    src_file = tmp_path / "file.txt"
    src_file.write_text("test")
    dest_dir = tmp_path / "dest"
    
    mock_copy.side_effect = PermissionError("Permission denied mock")

    res = copy_item(str(src_file), str(dest_dir))
    assert res["status"] == "error"
    assert res["error_class"] == "PermissionError"
    assert "Permission denied" in res["message"]


@patch("shutil.move")
def test_move_permission_error(mock_move, tmp_path):
    src_file = tmp_path / "file.txt"
    src_file.write_text("test")
    dest_dir = tmp_path / "dest"
    
    mock_move.side_effect = PermissionError("Permission denied mock")

    res = move_item(str(src_file), str(dest_dir))
    assert res["status"] == "error"
    assert res["error_class"] == "PermissionError"
    assert "Permission denied" in res["message"]
