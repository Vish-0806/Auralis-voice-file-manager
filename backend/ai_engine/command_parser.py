import re
from typing import Dict


FILLER_PATTERNS = [
    r"please",
    r"can you",
    r"could you",
    r"would you",
    r"my",
    r"the",
    r"a",
]

# normalize singular -> preferred folder names
NORMALIZE = {
    "download": "downloads",
    "downloads": "downloads",
    "document": "documents",
    "documents": "documents",
    "picture": "pictures",
    "pictures": "pictures",
    "photo": "pictures",
    "photos": "pictures",
    "video": "videos",
    "videos": "videos",
    "desktop": "desktop",
    "music": "music",
}


def _clean_text(text: str) -> str:
    t = text.lower()
    # remove punctuation
    t = re.sub(r"[\.,!?;:]", "", t)

    # remove filler phrases
    for p in FILLER_PATTERNS:
        t = re.sub(r"\b" + p + r"\b", "", t)

    # collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _normalize_target(target: str) -> str:
    t = target.strip().lower()
    # strip common trailing words like 'folder' or 'directory'
    t = re.sub(r"\b(folder|directory)\b", "", t).strip()
    # strip polite/filler single words that might remain
    t = re.sub(r"\b(please|my|the|a|an|could you|can you|would you)\b", "", t).strip()
    # map known folder names
    if t in NORMALIZE:
        return NORMALIZE[t]

    # singular to plural naive handling (e.g., "download" -> "downloads")
    if t.endswith("s"):
        return t
    if t in ["download", "document", "picture", "photo", "video"]:
        return NORMALIZE.get(t, t + "s")

    return t


def parse_command(command: str) -> Dict[str, str]:
    """Rule-based parser for simple natural-language file commands.

    Returns a dict with `action` and `target` keys.
    """
    if not isinstance(command, str) or not command.strip():
        return {"action": "unknown", "target": ""}

    text = _clean_text(command)

    # common action patterns
    # create folder / make folder / create directory
    if re.search(r"\b(create|make) (folder|directory)\b", text):
        # extract remainder after the phrase
        m = re.search(r"\b(?:create|make) (?:folder|directory)\b\s*(.*)", text)
        target = (m.group(1) if m else "").strip()
        target = _normalize_target(target) if target else target
        return {"action": "create_folder", "target": target}

    # open commands
    if re.search(r"\b(open|show|go to|navigate to)\b", text):
        # extract the noun after the action
        m = re.search(r"\b(?:open|show|go to|navigate to)\b\s*(.*)", text)
        target = (m.group(1) if m else "").strip()
        target = _normalize_target(target)
        return {"action": "open", "target": target}

    # delete/remove commands
    if re.search(r"\b(delete|remove|trash|remove)\b", text):
        m = re.search(r"\b(?:delete|remove|trash)\b\s*(.*)", text)
        target = (m.group(1) if m else "").strip()
        target = _normalize_target(target)
        return {"action": "delete", "target": target}

    return {"action": "unknown", "target": command.strip()}
