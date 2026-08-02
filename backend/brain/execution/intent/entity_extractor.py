"""Entity Extractor for the Auralis Intent Resolution Subsystem (Phase 12.2).

Extracts structured IntentEntity models from user prompt text for:
- PATH
- FILE
- FOLDER
- APPLICATION
- NUMBER
- DATE
- TIME
- WINDOW_NAME
- DEVICE_NAME
- KEYBOARD_SHORTCUT
"""

import re
from typing import Any, Dict, List

from brain.execution.intent.intent_models import EntityType, IntentEntity
from brain.execution.intent.interfaces import IEntityExtractor

# Pre-defined app names
KNOWN_APPLICATIONS = [
    "chrome", "firefox", "edge", "safari", "brave",
    "vs code", "vscode", "visual studio code", "pycharm", "intellij",
    "notepad", "notepad++", "word", "excel", "powerpoint",
    "explorer", "file explorer", "finder",
    "terminal", "cmd", "powershell", "bash",
    "calculator", "spotify", "slack", "discord", "teams", "zoom",
]

KNOWN_DEVICES = [
    "wifi", "wi-fi", "bluetooth", "speaker", "speakers",
    "microphone", "mic", "display", "monitor", "webcam", "camera",
]

KNOWN_WINDOWS = [
    "main window", "active window", "current window", "browser window",
    "focused window", "terminal window", "editor window",
]


class EntityExtractor(IEntityExtractor):
    """Deterministic entity extractor identifying paths, files, folders, apps, numbers, dates, and times."""

    def extract_entities(self, text: str) -> List[IntentEntity]:
        """Extract structured parameter entities from text.

        Args:
            text: Raw or normalized prompt text.

        Returns:
            List of extracted IntentEntity objects.
        """
        if not text or not text.strip():
            return []

        entities: List[IntentEntity] = []

        # 1. PATH extraction (Windows & POSIX paths)
        path_matches = re.finditer(
            r"\b([a-zA-Z]:[\\/][^\s]+|/(?:[^\s/]+/)+[^\s/]*|\./[^\s]+|\.\./[^\s]+)\b",
            text,
        )
        for match in path_matches:
            val = match.group(1)
            entities.append(
                IntentEntity(
                    entity_type=EntityType.PATH,
                    name="path",
                    value=val,
                    confidence=0.95,
                    position=(match.start(), match.end()),
                )
            )

        # 2. FILE extraction (filenames with extension)
        file_matches = re.finditer(
            r"\b([a-zA-Z0-9_\-\s]+\.(?:pdf|txt|docx?|xlsx?|pptx?|csv|json|py|js|html|png|jpg|jpeg|mp3|mp4|zip|tar|gz))\b",
            text,
            flags=re.IGNORECASE,
        )
        for match in file_matches:
            filename = match.group(1).strip()
            # Avoid duplicating if already matched as PATH
            if not any(e.entity_type == EntityType.PATH and filename in str(e.value) for e in entities):
                entities.append(
                    IntentEntity(
                        entity_type=EntityType.FILE,
                        name="filename",
                        value=filename,
                        confidence=0.90,
                        position=(match.start(), match.end()),
                    )
                )

        # 3. FOLDER extraction
        folder_matches = re.finditer(
            r"\b(folder|directory)\s+([a-zA-Z0-9_\-\s]+?)(?=\s+to|\s+in|\s+from|\s*$)",
            text,
            flags=re.IGNORECASE,
        )
        for match in folder_matches:
            foldername = match.group(2).strip()
            if foldername and foldername.lower() not in {"named", "called"}:
                entities.append(
                    IntentEntity(
                        entity_type=EntityType.FOLDER,
                        name="foldername",
                        value=foldername,
                        confidence=0.85,
                        position=(match.start(), match.end()),
                    )
                )

        # Standalone common folder names
        for common_folder in ["downloads", "documents", "desktop", "pictures", "videos", "music"]:
            if re.search(r"\b" + common_folder + r"\b", text, flags=re.IGNORECASE):
                if not any(e.entity_type == EntityType.FOLDER and common_folder in str(e.value).lower() for e in entities):
                    entities.append(
                        IntentEntity(
                            entity_type=EntityType.FOLDER,
                            name="foldername",
                            value=common_folder.capitalize(),
                            confidence=0.90,
                        )
                    )

        # 4. APPLICATION extraction
        text_lower = text.lower()
        for app in KNOWN_APPLICATIONS:
            if re.search(r"\b" + re.escape(app) + r"\b", text_lower):
                entities.append(
                    IntentEntity(
                        entity_type=EntityType.APPLICATION,
                        name="app_name",
                        value=app,
                        confidence=0.90,
                    )
                )

        # 5. DEVICE extraction
        for dev in KNOWN_DEVICES:
            if re.search(r"\b" + re.escape(dev) + r"\b", text_lower):
                entities.append(
                    IntentEntity(
                        entity_type=EntityType.DEVICE_NAME,
                        name="device_name",
                        value=dev,
                        confidence=0.85,
                    )
                )

        # 6. WINDOW extraction
        for win in KNOWN_WINDOWS:
            if win in text_lower:
                entities.append(
                    IntentEntity(
                        entity_type=EntityType.WINDOW_NAME,
                        name="window_name",
                        value=win,
                        confidence=0.85,
                    )
                )

        # 7. NUMBER extraction
        num_matches = re.finditer(r"\b(\d+(?:\.\d+)?%?)", text)
        for match in num_matches:
            val_str = match.group(1)
            # Filter out numbers that are part of dates or filenames
            if not any(match.start() >= e.position[0] and match.end() <= e.position[1] for e in entities if e.position):
                is_pct = val_str.endswith("%")
                clean_num_str = val_str[:-1] if is_pct else val_str
                parsed_val: Any = float(clean_num_str) if "." in clean_num_str else int(clean_num_str)
                entities.append(
                    IntentEntity(
                        entity_type=EntityType.NUMBER,
                        name="number",
                        value=parsed_val,
                        confidence=0.95,
                        position=(match.start(), match.end()),
                        metadata={"is_percentage": is_pct},
                    )
                )

        # 8. DATE extraction
        date_matches = re.finditer(
            r"\b(today|yesterday|tomorrow|next monday|next tuesday|next wednesday|next thursday|next friday|next saturday|next sunday|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b",
            text,
            flags=re.IGNORECASE,
        )
        for match in date_matches:
            entities.append(
                IntentEntity(
                    entity_type=EntityType.DATE,
                    name="date",
                    value=match.group(1).lower(),
                    confidence=0.90,
                    position=(match.start(), match.end()),
                )
            )

        # 9. TIME extraction
        time_matches = re.finditer(
            r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm)?|\d{1,2}\s*(?:am|pm)|\d+\s*(?:seconds?|minutes?|hours?|sec|min|hrs))\b",
            text,
            flags=re.IGNORECASE,
        )
        for match in time_matches:
            entities.append(
                IntentEntity(
                    entity_type=EntityType.TIME,
                    name="time",
                    value=match.group(1).lower(),
                    confidence=0.90,
                    position=(match.start(), match.end()),
                )
            )

        # 10. KEYBOARD SHORTCUT extraction
        shortcut_match = re.search(r"\b(ctrl|alt|shift|cmd|win)\s*\+\s*([a-z0-9]+)\b", text, flags=re.IGNORECASE)
        if shortcut_match:
            entities.append(
                IntentEntity(
                    entity_type=EntityType.KEYBOARD_SHORTCUT,
                    name="shortcut",
                    value=shortcut_match.group(0).lower(),
                    confidence=0.95,
                )
            )

        return entities
