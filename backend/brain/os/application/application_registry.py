"""Application Registry implementation (Phase 11.3).

Provides thread-safe in-memory caching, registration, unregistration, alias resolution,
executable lookup, and categorization for installed desktop applications.
"""

from datetime import datetime, timezone
import threading
from typing import Dict, List, Optional

from brain.os.application.application_models import (
    ApplicationInfo,
    ApplicationRegistryEntry,
    InstalledApplication,
)
from brain.os.application.interfaces import IApplicationRegistry


class ApplicationRegistry(IApplicationRegistry):
    """Thread-safe application registry for tracking installed applications and aliases."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._apps_by_id: Dict[str, InstalledApplication] = {}
        self._name_to_id: Dict[str, str] = {}
        self._alias_to_id: Dict[str, str] = {}
        self._exec_to_id: Dict[str, str] = {}
        self._entries: Dict[str, ApplicationRegistryEntry] = {}

    def register_application(self, app: InstalledApplication) -> ApplicationRegistryEntry:
        """Register or update an application in the registry."""
        with self._lock:
            info = app.info
            app_id = info.app_id or info.name.lower().replace(" ", "_")

            # Update info model if app_id was missing
            if not info.app_id:
                info = ApplicationInfo(
                    app_id=app_id,
                    name=info.name,
                    display_name=info.display_name or info.name,
                    executable_path=info.executable_path,
                    version=info.version,
                    publisher=info.publisher,
                    category=info.category,
                    aliases=info.aliases,
                    description=info.description,
                )
                app = InstalledApplication(
                    info=info,
                    install_path=app.install_path,
                    is_system_app=app.is_system_app,
                    icon_path=app.icon_path,
                    categories=app.categories,
                )

            self._apps_by_id[app_id] = app
            self._name_to_id[info.name.lower()] = app_id

            if info.executable_path:
                norm_exec = info.executable_path.lower().replace("/", "\\")
                self._exec_to_id[norm_exec] = app_id

            for alias in info.aliases:
                self._alias_to_id[alias.lower()] = app_id

            reg_entry = ApplicationRegistryEntry(
                app_id=app_id,
                name=info.name,
                executable_path=info.executable_path,
                aliases=info.aliases,
                category=info.category,
                registered_at=datetime.now(timezone.utc),
            )
            self._entries[app_id] = reg_entry
            return reg_entry

    def unregister_application(self, app_id_or_name: str) -> bool:
        """Remove an application from the registry."""
        with self._lock:
            key = app_id_or_name.lower()
            app_id = key
            if key not in self._apps_by_id:
                app_id = self._name_to_id.get(key) or self._alias_to_id.get(key) or ""

            if not app_id or app_id not in self._apps_by_id:
                return False

            app = self._apps_by_id.pop(app_id, None)
            self._entries.pop(app_id, None)

            if app:
                self._name_to_id.pop(app.info.name.lower(), None)
                if app.info.executable_path:
                    self._exec_to_id.pop(app.info.executable_path.lower().replace("/", "\\"), None)
                for alias in app.info.aliases:
                    self._alias_to_id.pop(alias.lower(), None)

            return True

    def get_application(self, app_id_or_name: str) -> Optional[InstalledApplication]:
        """Lookup an application by ID or primary name."""
        with self._lock:
            key = app_id_or_name.lower()
            if key in self._apps_by_id:
                return self._apps_by_id[key]

            app_id = self._name_to_id.get(key) or self._alias_to_id.get(key)
            if app_id:
                return self._apps_by_id.get(app_id)
            return None

    def get_by_executable(self, executable_path: str) -> Optional[InstalledApplication]:
        """Lookup an application by executable path."""
        with self._lock:
            norm = executable_path.lower().replace("/", "\\")
            app_id = self._exec_to_id.get(norm)
            if app_id:
                return self._apps_by_id.get(app_id)
            return None

    def get_by_alias(self, alias: str) -> Optional[InstalledApplication]:
        """Lookup an application by alias."""
        with self._lock:
            app_id = self._alias_to_id.get(alias.lower())
            if app_id:
                return self._apps_by_id.get(app_id)
            return None

    def list_applications(self, category: Optional[str] = None) -> List[InstalledApplication]:
        """List all registered applications, optionally filtered by category."""
        with self._lock:
            apps = list(self._apps_by_id.values())
            if not category:
                return apps
            cat_lower = category.lower()
            return [
                a for a in apps
                if a.info.category.lower() == cat_lower or any(c.lower() == cat_lower for c in a.categories)
            ]
