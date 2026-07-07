"""Unit tests for the context awareness subsystem."""

import pytest

from voice.context.models import ContextState, ResolutionResult
from voice.context.memory import TemporaryMemory
from voice.context.reference_resolver import ReferenceResolver
from voice.context.context_manager import ContextManager


def test_context_state_initialization():
    """Verify that ContextState fields start empty."""
    state = ContextState()
    assert state.current_file is None
    assert state.current_folder is None
    assert state.current_search_results == []
    assert state.current_capability is None
    assert state.last_intent is None
    assert state.last_execution_result is None
    assert state.pending_confirmation is None


def test_temporary_memory_operations():
    """Verify set, get, delete, and clear operations in TemporaryMemory."""
    mem = TemporaryMemory()
    assert mem.get("key1") is None
    assert mem.get("key1", default="abc") == "abc"

    mem.set("key1", "val1")
    assert mem.get("key1") == "val1"

    assert mem.delete("key1") is True
    assert mem.get("key1") is None
    assert mem.delete("key1") is False

    mem.set("k2", "v2")
    mem.set("k3", "v3")
    mem.clear()
    assert mem.get("k2") is None
    assert mem.get("k3") is None


def test_pronoun_resolution_rules():
    """Verify pronoun resolution (it, that, this, those) and ambiguity detection."""
    resolver = ReferenceResolver()
    context = ContextState()

    # Case 1: Neither file nor folder is set
    res = resolver.resolve("open it", context)
    assert res.requires_clarification is True
    assert "I couldn't resolve what you're referring to" in res.clarification_prompt

    # Case 2: Only file is set
    context.current_file = "notes.txt"
    res = resolver.resolve("delete it", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "delete notes.txt"

    # Case 3: Only folder is set
    context.current_file = None
    context.current_folder = "downloads"
    res = resolver.resolve("open that", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "open downloads"

    # Case 4: Both are set (Ambiguous!)
    context.current_file = "notes.txt"
    context.current_folder = "downloads"
    res = resolver.resolve("remove this", context)
    assert res.requires_clarification is True
    assert "I see both a file" in res.clarification_prompt


def test_ordinal_resolution_rules():
    """Verify ordinal resolution (the first one, the second one, the last file/one)."""
    resolver = ReferenceResolver()
    context = ContextState()

    # Empty search list
    res = resolver.resolve("open the first one", context)
    assert res.requires_clarification is True
    assert "select the first item" in res.clarification_prompt

    # Populate search results
    context.current_search_results = ["first.txt", "second.png", "third.pdf"]

    # "the first one"
    res = resolver.resolve("delete the first one", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "delete first.txt"

    # "the second one"
    res = resolver.resolve("open the second one", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "open second.png"

    # "the last one"
    res = resolver.resolve("move the last one", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "move third.pdf"

    # "the last file"
    res = resolver.resolve("copy the last file", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "copy third.pdf"


def test_specific_noun_resolution_rules():
    """Verify resolving specific nouns (the folder, the document, the image)."""
    resolver = ReferenceResolver()
    context = ContextState()

    # "the folder"
    res = resolver.resolve("open the folder", context)
    assert res.requires_clarification is True  # folder not set
    context.current_folder = "my_projects"
    res = resolver.resolve("open the folder", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "open my_projects"

    # "the document" (file active)
    context.current_file = "report.docx"
    res = resolver.resolve("read the document", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "read report.docx"

    # "the document" (via search results)
    context.current_file = "photo.jpg"  # not a doc
    context.current_search_results = ["photo.jpg", "summary.txt"]
    res = resolver.resolve("open the document", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "open summary.txt"

    # "the document" (multiple documents - ambiguous!)
    context.current_search_results = ["photo.jpg", "summary.txt", "notes.pdf"]
    res = resolver.resolve("open the document", context)
    assert res.requires_clarification is True
    assert "multiple documents" in res.clarification_prompt

    # "the image" (file active)
    context.current_file = "avatar.png"
    res = resolver.resolve("display the image", context)
    assert res.requires_clarification is False
    assert res.resolved_command == "display avatar.png"

    # "the image" (via search results)
    context.current_file = "summary.txt"
    context.current_search_results = ["summary.txt", "cat.webp"]
    res = resolver.resolve("show the image", context)
    assert res.requires_clarification == False
    assert res.resolved_command == "show cat.webp"


def test_context_manager_operations():
    """Verify ContextManager updating, resolving, and automatic clearing."""
    cm = ContextManager()

    # Update state and memory
    cm.update(current_file="todo.txt", current_folder="todo_dir")
    cm.memory.set("user_id", "456")

    assert cm.state.current_file == "todo.txt"
    assert cm.state.current_folder == "todo_dir"
    assert cm.memory.get("user_id") == "456"

    # Test clearing
    cm.clear()
    assert cm.state.current_file is None
    assert cm.state.current_folder is None
    assert cm.memory.get("user_id") is None
