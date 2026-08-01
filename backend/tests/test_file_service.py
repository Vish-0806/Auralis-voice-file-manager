"""Unit tests for FileService (Phase 11.2)."""

import pytest
from brain.os.filesystem import FileService, OperationStatus
from brain.os.filesystem.exceptions import FileExistsError, FileNotFoundError


def test_file_service_text_rw(tmp_path) -> None:
    f_path = tmp_path / "hello.txt"
    svc = FileService()

    res = svc.write_text(str(f_path), "Hello Auralis", atomic=True)
    assert res.status == OperationStatus.SUCCESS
    assert res.bytes_affected > 0

    content = svc.read_text(str(f_path))
    assert content == "Hello Auralis"


def test_file_service_bytes_rw(tmp_path) -> None:
    f_path = tmp_path / "data.bin"
    svc = FileService()

    res = svc.write_bytes(str(f_path), b"\x00\x01\x02\x03", atomic=True)
    assert res.status == OperationStatus.SUCCESS

    data = svc.read_bytes(str(f_path))
    assert data == b"\x00\x01\x02\x03"


def test_file_service_copy_move_rename_delete(tmp_path) -> None:
    src = tmp_path / "source.txt"
    src.write_text("initial text")

    svc = FileService()

    # Copy
    cp_dst = tmp_path / "copied.txt"
    cp_res = svc.copy_file(str(src), str(cp_dst))
    assert cp_res.status == OperationStatus.SUCCESS
    assert cp_dst.read_text() == "initial text"

    # Rename
    ren_res = svc.rename_file(str(cp_dst), "renamed.txt")
    assert ren_res.status == OperationStatus.SUCCESS
    assert (tmp_path / "renamed.txt").exists()

    # Move
    mv_dst = tmp_path / "sub" / "moved.txt"
    mv_res = svc.move_file(str(src), str(mv_dst))
    assert mv_res.status == OperationStatus.SUCCESS
    assert mv_dst.exists()
    assert not src.exists()

    # Delete
    del_res = svc.delete_file(str(mv_dst))
    assert del_res.status == OperationStatus.SUCCESS
    assert not mv_dst.exists()


def test_file_service_overwrite_policy(tmp_path) -> None:
    f = tmp_path / "existing.txt"
    f.write_text("old data")

    svc = FileService()
    with pytest.raises(FileExistsError):
        svc.write_text(str(f), "new data", overwrite=False)
