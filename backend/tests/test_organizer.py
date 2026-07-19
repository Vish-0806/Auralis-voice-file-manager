import os
import shutil
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch, MagicMock
from capabilities.files.file_operations import get_category_for_file, organize_directory, execute_action
from utils.helpers import format_speak_message


def test_get_category_for_file():
    assert get_category_for_file("report.pdf") == "PDFs"
    assert get_category_for_file("image.JPEG") == "Images"
    assert get_category_for_file("video.mp4") == "Videos"
    assert get_category_for_file("doc.docx") == "Documents"
    assert get_category_for_file("archive.tar.gz") == "Archives"
    assert get_category_for_file("script.py") == "Code"
    assert get_category_for_file("unknown.xyz") == "Others"
    assert get_category_for_file("no_extension") == "Others"


def test_organize_directory_basic(tmp_path):
    # Setup test files
    pdf_file = tmp_path / "test.pdf"
    png_file = tmp_path / "test.png"
    txt_file = tmp_path / "test.txt"
    py_file = tmp_path / "test.py"
    zip_file = tmp_path / "test.zip"
    mp4_file = tmp_path / "test.mp4"
    abc_file = tmp_path / "test.abc"

    for f in [pdf_file, png_file, txt_file, py_file, zip_file, mp4_file, abc_file]:
        f.write_text("dummy content")

    # Run organizer
    summary = organize_directory(str(tmp_path))

    # Assert summary
    assert summary["moved_files"] == 7
    assert summary["categories_created"] == 7

    # Assert files are moved to appropriate folders
    assert (tmp_path / "PDFs" / "test.pdf").exists()
    assert (tmp_path / "Images" / "test.png").exists()
    assert (tmp_path / "Documents" / "test.txt").exists()
    assert (tmp_path / "Code" / "test.py").exists()
    assert (tmp_path / "Archives" / "test.zip").exists()
    assert (tmp_path / "Videos" / "test.mp4").exists()
    assert (tmp_path / "Others" / "test.abc").exists()

    # Original files should not exist at root level
    assert not pdf_file.exists()


def test_organize_directory_skip_subdirs(tmp_path):
    # Setup files and a subdirectory
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy pdf")

    sub_dir = tmp_path / "SubFolder"
    sub_dir.mkdir()
    sub_pdf = sub_dir / "ignored.pdf"
    sub_pdf.write_text("should be skipped")

    # Run organizer
    summary = organize_directory(str(tmp_path))

    # Assert only the root level PDF is moved
    assert summary["moved_files"] == 1
    assert (tmp_path / "PDFs" / "test.pdf").exists()
    # The SubFolder itself should still exist and not be moved or inside PDFs
    assert sub_dir.exists()
    assert not (tmp_path / "PDFs" / "SubFolder").exists()
    assert sub_pdf.exists()


def test_organize_directory_duplicate_handling(tmp_path):
    # Create target directory PDFs and a file inside it
    pdf_dir = tmp_path / "PDFs"
    pdf_dir.mkdir()
    existing_pdf = pdf_dir / "test.pdf"
    existing_pdf.write_text("first draft")

    # Create root level file with same name
    root_pdf = tmp_path / "test.pdf"
    root_pdf.write_text("second draft")

    # Run organizer
    summary = organize_directory(str(tmp_path))

    # Assert it was moved
    assert summary["moved_files"] == 1
    # Category folder already existed, so no categories created
    assert summary["categories_created"] == 0

    # The root file should be renamed to test_1.pdf
    assert existing_pdf.exists()
    assert (pdf_dir / "test_1.pdf").exists()
    assert not root_pdf.exists()


def test_organize_directory_permission_error(tmp_path):
    # Create two files
    file1 = tmp_path / "file1.pdf"
    file1.write_text("file1 content")
    file2 = tmp_path / "file2.png"
    file2.write_text("file2 content")

    # Mock shutil.move to raise PermissionError only for file1
    def mock_move(src, dst):
        if "file1.pdf" in src:
            raise PermissionError("Access Denied")
        # Default behavior
        shutil._orig_move(src, dst)

    # Backup the original move and patch
    shutil._orig_move = shutil.move
    try:
        with patch("shutil.move", side_effect=mock_move):
            summary = organize_directory(str(tmp_path))

        # Only file2.png should be moved; file1.pdf should be skipped due to permission error
        assert summary["moved_files"] == 1
        assert summary["categories_created"] == 2
        assert file1.exists()
        assert (tmp_path / "Images" / "file2.png").exists()
    finally:
        shutil.move = shutil._orig_move


def test_execute_action_organize(tmp_path):
    # Setup test file
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("some notes")

    # Mock get_target_path to return our temp dir
    with patch("capabilities.files.file_operations.get_target_path", return_value=str(tmp_path)):
        action_data = {"action": "organize", "target": "downloads"}
        
        # Step 1: Initial organize request (requires confirmation)
        result = execute_action(action_data)
        assert isinstance(result, dict)
        assert result["status"] == "pending_confirmation"
        assert result["message"] == "Are you sure you want to organize downloads?"

        # Step 2: Confirm
        confirm_res = execute_action({"action": "confirm", "target": ""})
        assert confirm_res == "Successfully organized Downloads folder. Moved 1 files into 1 categories."
        assert (tmp_path / "Documents" / "notes.txt").exists()


def test_helpers_speak_message_organize():
    parsed_action = {"action": "organize", "target": "downloads"}
    result_dict = {"moved_files": 12, "categories_created": 4}

    message = format_speak_message(result_dict, parsed_action)
    assert message == "I organized your downloads folder. Moved 12 files into 4 categories."

    # Non-dict fallback
    assert format_speak_message("some error string", parsed_action) == "I organized your downloads folder."
