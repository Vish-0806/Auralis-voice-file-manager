"""Unit tests for MetadataService (Phase 11.2)."""

import pytest
from brain.os.filesystem import DirectoryMetadata, FileMetadata, MetadataService


def test_metadata_service_file(tmp_path) -> None:
    test_file = tmp_path / "document.pdf"
    test_file.write_bytes(b"%PDF-1.4 sample content")

    svc = MetadataService()
    meta = svc.get_file_metadata(str(test_file))

    assert isinstance(meta, FileMetadata)
    assert meta.name == "document.pdf"
    assert meta.extension == ".pdf"
    assert meta.size_bytes > 0
    assert meta.mime_type == "application/pdf"
    assert meta.is_hidden is False
    assert meta.created_at is not None
    assert meta.modified_at is not None


def test_metadata_service_directory(tmp_path) -> None:
    test_dir = tmp_path / "sub_folder"
    test_dir.mkdir()

    (test_dir / "f1.txt").write_text("content1")
    (test_dir / "f2.txt").write_text("content2")

    svc = MetadataService()
    dir_meta = svc.get_directory_metadata(str(test_dir))

    assert isinstance(dir_meta, DirectoryMetadata)
    assert dir_meta.name == "sub_folder"
    assert dir_meta.child_count == 2
    assert dir_meta.is_empty is False
    assert dir_meta.total_size_bytes > 0


def test_metadata_service_helpers(tmp_path) -> None:
    svc = MetadataService()
    file1 = tmp_path / "image.png"
    file1.write_bytes(b"\x89PNG")

    assert svc.get_mime_type(str(file1)) == "image/png"
    assert svc.is_hidden(str(file1)) is False
    assert svc.is_symlink(str(file1)) is False
