import os
import pytest
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.intents import Intent
from core.models import AssistantRequest, ExecutionPlan
from core.planner import Planner
from capabilities.files.file_capability import FileCapability
from capabilities.files.organizer.organization_rules import OrganizationRules
from capabilities.files.organizer.file_classifier import FileClassifier
from capabilities.files.organizer.report_generator import ReportGenerator
from capabilities.files.organizer.download_organizer import DownloadOrganizer


def test_file_classifier():
    rules = OrganizationRules()
    classifier = FileClassifier(rules)

    assert classifier.classify(Path("test.pdf")) == "PDF"
    assert classifier.classify(Path("notes.txt")) == "Text"
    assert classifier.classify(Path("script.py")) == "Code"
    assert classifier.classify(Path("sheet.xlsx")) == "Spreadsheets"
    assert classifier.classify(Path("image.png")) == "Images"
    assert classifier.classify(Path("video.mp4")) == "Videos"
    assert classifier.classify(Path("song.mp3")) == "Audio"
    assert classifier.classify(Path("archive.zip")) == "Archives"
    assert classifier.classify(Path("installer.exe")) == "Executables"
    assert classifier.classify(Path("presentation.pptx")) == "Presentations"
    assert classifier.classify(Path("doc.docx")) == "Documents"
    assert classifier.classify(Path("unknown.xyz")) == "Others"


def test_report_generator():
    report = ReportGenerator()
    report.log_scanned("file1.pdf")
    report.log_moved("file1.pdf", "PDF/file1.pdf", "PDF")
    report.log_skipped("desktop.ini", "Hidden or system file")
    report.log_error("locked.txt", "Permission denied")

    summary = report.generate_summary()
    assert "Files Scanned: 1" in summary
    assert "Files Organized: 1" in summary
    assert "Files Skipped: 1" in summary
    assert "Errors: 1" in summary
    assert "PDF: 1 file(s)" in summary

    data = report.get_data()
    assert data["scanned_count"] == 1
    assert data["moved_count"] == 1
    assert data["skipped_count"] == 1
    assert data["error_count"] == 1


def test_download_organizer_sorting(tmp_path):
    # Setup files in tmp Downloads folder
    pdf_file = tmp_path / "report.pdf"
    pdf_file.write_text("pdf data")

    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("text data")

    # Existing category directory
    (tmp_path / "PDF").mkdir()

    organizer = DownloadOrganizer()
    res = organizer.organize(tmp_path)

    assert res["status"] == "success"
    assert (tmp_path / "PDF" / "report.pdf").exists()
    assert (tmp_path / "Text" / "notes.txt").exists()
    assert not pdf_file.exists()
    assert not txt_file.exists()


def test_download_organizer_duplicate_resolution(tmp_path):
    # Create target folder and pre-existing file in it
    pdf_dir = tmp_path / "PDF"
    pdf_dir.mkdir()
    (pdf_dir / "report.pdf").write_text("old")

    # Source file with same name
    src_file = tmp_path / "report.pdf"
    src_file.write_text("new")

    organizer = DownloadOrganizer()
    res = organizer.organize(tmp_path)

    assert res["status"] == "success"
    assert (pdf_dir / "report.pdf").exists()
    assert (pdf_dir / "report_1.pdf").exists()
    assert (pdf_dir / "report_1.pdf").read_text() == "new"


def test_download_organizer_skip_hidden_and_system(tmp_path):
    # Setup normal file
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("text")

    # Setup unix dotfile (hidden)
    hidden_file = tmp_path / ".secret"
    hidden_file.write_text("hidden")

    # Setup windows system file
    system_file = tmp_path / "desktop.ini"
    system_file.write_text("system config")

    organizer = DownloadOrganizer()
    res = organizer.organize(tmp_path)

    assert res["status"] == "success"
    assert (tmp_path / "Text" / "notes.txt").exists()
    assert hidden_file.exists()
    assert system_file.exists()

    data = res["data"]
    assert data["moved_count"] == 1
    assert data["skipped_count"] == 2


def test_planner_organize_intent():
    planner = Planner()

    req1 = AssistantRequest(message="Organize my Downloads", source="test", timestamp=datetime.now(UTC))
    plan1 = planner.create_plan(req1)
    assert plan1.intent == Intent.ORGANIZE_FOLDER
    assert plan1.target == "Downloads"

    req2 = AssistantRequest(message="clean downloads", source="test", timestamp=datetime.now(UTC))
    plan2 = planner.create_plan(req2)
    assert plan2.intent == Intent.ORGANIZE_FOLDER
    assert plan2.target == "Downloads"


def test_file_capability_organize(tmp_path):
    capability = FileCapability()

    # Setup files in tmp_path to organize
    (tmp_path / "test.pdf").write_text("pdf data")

    with patch.object(capability._path_resolver, "resolve", return_value=str(tmp_path)):
        plan = ExecutionPlan(
            intent=Intent.ORGANIZE_FOLDER,
            target="Downloads",
            parameters={},
            confidence=0.9
        )
        res = capability.execute_plan(plan)
        assert res.success is True
        assert "Files Organized: 1" in res.response
        assert (tmp_path / "PDF" / "test.pdf").exists()
