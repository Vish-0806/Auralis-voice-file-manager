"""Unit tests for ClipboardService (Phase 11.5)."""

# pyrefly: ignore [missing-import]
import pytest
from brain.os.desktop import ClipboardContent, ClipboardFormat, ClipboardService


def test_clipboard_service_write_and_read_text() -> None:
    svc = ClipboardService()

    success = svc.write_text("Test clipboard content")
    assert success is True

    content = svc.read_content()
    assert isinstance(content, ClipboardContent)
    assert content.format == ClipboardFormat.TEXT
    assert content.text_content == "Test clipboard content"


def test_clipboard_service_write_files_and_clear() -> None:
    svc = ClipboardService()

    files = ["/path/to/file1.txt", "/path/to/file2.txt"]
    success = svc.write_files(files)
    assert success is True

    content = svc.read_content()
    assert content.format == ClipboardFormat.FILES or content.format == ClipboardFormat.TEXT
    if content.format == ClipboardFormat.FILES:
        assert content.file_paths == files

    cleared = svc.clear()
    assert cleared is True
