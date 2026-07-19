import os
import sys

# Monkeypatch standard library os to recognize the local os folder as a package
backend_dir = os.path.dirname(os.path.abspath(__file__))
local_os_path = os.path.join(backend_dir, "os")
if os.path.isdir(local_os_path):
    os.__path__ = [local_os_path]


# pyrefly: ignore [missing-import]
import pytest

@pytest.fixture(autouse=True)
def force_in_memory_provider_for_tests(monkeypatch):
    """Force Auralis memory provider to in_memory during automated tests to isolate them from PostgreSQL."""
    from memory.config import settings
    monkeypatch.setattr(settings, "provider_type", "in_memory")
