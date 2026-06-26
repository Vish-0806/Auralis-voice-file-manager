import os
import sys

# Monkeypatch standard library os to recognize the local os folder as a package
backend_dir = os.path.dirname(os.path.abspath(__file__))
local_os_path = os.path.join(backend_dir, "os")
if os.path.isdir(local_os_path):
    os.__path__ = [local_os_path]
