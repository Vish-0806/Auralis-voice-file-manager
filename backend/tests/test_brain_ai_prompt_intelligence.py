"""Comprehensive Unit Tests for Phase 10.3: Prompt Intelligence.

Validates:
- ConversationBuilder: History ordering, provider formatting, message limits, oldest-first trimming, system prompt preservation
- MemoryInjector: Long-term memory, recent memory, preferences, pinned memory, execution context
- WorkspaceContextInjector: Current directory, selected files, OS, active workspace, environment metadata
- PromptTemplates: System, Developer, Memory, Workspace template rendering and custom overrides
- TokenEstimator: Character counts, estimated tokens (~4 chars/token + overhead), breakdown metrics
- PromptOptimizer: Layer merging, deduplication, priority order (System > Developer > Memory > Workspace > Conversation > User)
- Edge cases: Large prompt trimming, empty prompts, duplicate messages, malformed context
"""

# pyrefly: ignore [missing-import]
import pytest
from typing import Any, Dict

from brain.ai import (
    AIContext,
    ConversationBuilder,
    DefaultContextBuilder,
    DefaultMemoryProvider,
    DefaultPromptBuilder,
    MemoryInjector,
    MockWorkspaceContextProvider,
    Prompt,
    PromptMessage,
    PromptOptimizer,
    PromptRole,
    PromptTemplates,
    ROLE_PRIORITY,
    TokenEstimator,
    WorkspaceContextInjector,
)
from brain.runtime.brain_models import BrainRequest


# ---------------------------------------------------------------------------
# Tests: PromptTemplates
# ---------------------------------------------------------------------------


def test_prompt_templates_default_rendering():
    """Test default template rendering for all prompt sections."""
    templates = PromptTemplates()

    sys_text = templates.render_system(assistant_name="Auralis")
    assert "Auralis" in sys_text

    dev_text = templates.render_developer()
    assert "safety" in dev_text.lower()

    mem_text = templates.render_memory(
        long_term="Prefers Python",
        recent="Created main.py",
        preferences="dark_mode",
        pinned="Project Root",
        execution="running",
    )
    assert "Prefers Python" in mem_text
    assert "Created main.py" in mem_text

    ws_text = templates.render_workspace(
        current_dir="/home/user/app",
        active_workspace="Auralis",
        operating_system="Windows",
        selected_files=["a.py", "b.py"],
        env_metadata={"env": "dev"},
    )
    assert "/home/user/app" in ws_text
    assert "Windows" in ws_text


def test_prompt_templates_custom_overrides():
    """Test custom template string overrides."""
    templates = PromptTemplates(
        system_template="Custom System: {assistant_name}",
        workspace_template="Custom Workspace: {current_dir}",
    )

    assert templates.render_system(assistant_name="Bot") == "Custom System: Bot"
    assert templates.render_workspace(current_dir="/tmp") == "Custom Workspace: /tmp"


# ---------------------------------------------------------------------------
# Tests: TokenEstimator
# ---------------------------------------------------------------------------


def test_token_estimator_character_and_token_counts():
    """Test character and token count estimation math."""
    estimator = TokenEstimator()

    # Empty string / None
    assert estimator.estimate_characters("") == 0
    assert estimator.estimate_tokens("") == 0
    assert estimator.estimate_tokens(None) == 0

    # Normal text (~4 chars per token)
    text = "Hello world from Auralis"  # 24 characters -> ~6 tokens
    assert estimator.estimate_characters(text) == 24
    assert estimator.estimate_tokens(text) == 6

    # PromptMessage (~4 chars per token + 4 overhead tokens)
    msg = PromptMessage(role=PromptRole.USER, content="Hello world from Auralis")
    msg_tokens = estimator.estimate_tokens(msg)
    assert msg_tokens == 6 + estimator.PER_MESSAGE_OVERHEAD_TOKENS  # 10 tokens

    # Prompt breakdown
    prompt = Prompt(
        system_prompt="System instructions",
        user_prompt="User query",
        formatted_messages=[msg],
    )
    breakdown = estimator.estimate_prompt_breakdown(prompt)
    assert breakdown["total_characters"] > 0
    assert breakdown["total_tokens"] > 0
    assert breakdown["message_count"] == 1
    assert "user" in breakdown["by_role"]


# ---------------------------------------------------------------------------
# Tests: ConversationBuilder
# ---------------------------------------------------------------------------


def test_conversation_builder_ordering_and_formatting():
    """Test conversation history ordering and provider dictionary formatting."""
    builder = ConversationBuilder(max_history_messages=5)
    raw_history = [
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I am doing well."},
        ("user", "Summarize project"),
    ]

    messages = builder.build_conversation(raw_history)
    assert len(messages) == 3
    assert messages[0].role == PromptRole.USER
    assert messages[1].role == PromptRole.ASSISTANT
    assert messages[2].content == "Summarize project"

    formatted = builder.format_messages_for_provider(messages)
    assert len(formatted) == 3
    assert formatted[0] == {"role": "user", "content": "How are you?"}
    assert formatted[1] == {"role": "assistant", "content": "I am doing well."}


def test_conversation_builder_trimming_oldest_first_and_system_preservation():
    """Test ConversationBuilder trims oldest chat messages while preserving system prompts."""
    builder = ConversationBuilder(max_history_messages=2)

    raw_history = [
        PromptMessage(role=PromptRole.SYSTEM, content="Keep system prompt"),
        {"role": "user", "content": "Message 1 (Oldest)"},
        {"role": "assistant", "content": "Message 2"},
        {"role": "user", "content": "Message 3 (Newest)"},
    ]

    messages = builder.build_conversation(raw_history)
    # Should preserve system message + last 2 chat messages
    assert len(messages) == 3
    assert messages[0].content == "Keep system prompt"
    assert messages[1].content == "Message 2"
    assert messages[2].content == "Message 3 (Newest)"


# ---------------------------------------------------------------------------
# Tests: MemoryInjector & WorkspaceContextInjector
# ---------------------------------------------------------------------------


def test_memory_injector_all_facets():
    """Test MemoryInjector extracts long-term, recent, preferences, pinned, and execution context."""
    injector = MemoryInjector()
    ctx = AIContext(
        request_id="req-mem-1",
        raw_query="Test query",
        memory_context={
            "long_term": "User is a Software Engineer",
            "recent": "Opened workspace",
            "user_preferences": {"theme": "dark"},
            "pinned": "Critical guidelines",
        },
        execution_context={"state": "active"},
    )

    mem_text = injector.inject_memory(ctx)
    assert "Software Engineer" in mem_text
    assert "Opened workspace" in mem_text
    assert "dark" in mem_text
    assert "Critical guidelines" in mem_text
    assert "active" in mem_text

    mem_msg = injector.build_memory_message(ctx)
    assert mem_msg is not None
    assert mem_msg.role == PromptRole.MEMORY


def test_workspace_context_injector_all_metadata():
    """Test WorkspaceContextInjector injects current dir, selected files, OS, workspace, and env."""
    mock_provider = MockWorkspaceContextProvider(
        default_dir="/projects/auralis",
        default_active_workspace="Auralis-Core",
        default_selected_files=["main.py", "README.md"],
        default_env_metadata={"os": "Windows 11"},
    )
    injector = WorkspaceContextInjector(workspace_provider=mock_provider)
    ctx = AIContext(request_id="req-ws-1", raw_query="Test")

    ws_text = injector.inject_workspace(ctx)
    assert "/projects/auralis" in ws_text
    assert "Auralis-Core" in ws_text
    assert "main.py" in ws_text

    ws_msg = injector.build_workspace_message(ctx)
    assert ws_msg is not None
    assert ws_msg.role == PromptRole.WORKSPACE


# ---------------------------------------------------------------------------
# Tests: PromptOptimizer (Deduplication & Priority Sorting)
# ---------------------------------------------------------------------------


def test_prompt_optimizer_priority_ordering_and_deduplication():
    """Test PromptOptimizer enforces System > Developer > Memory > Workspace > Conversation > User priority."""
    optimizer = PromptOptimizer()

    input_messages = [
        PromptMessage(role=PromptRole.USER, content="User Query"),
        PromptMessage(role=PromptRole.WORKSPACE, content="Workspace Info"),
        PromptMessage(role=PromptRole.SYSTEM, content="System Prompt"),
        PromptMessage(role=PromptRole.USER, content="User Query"),  # Duplicate
        PromptMessage(role=PromptRole.DEVELOPER, content="Developer Policy"),
        PromptMessage(role=PromptRole.MEMORY, content="Memory Facts"),
        PromptMessage(role=PromptRole.ASSISTANT, content="Past Assistant Response"),
    ]

    raw_prompt = Prompt(formatted_messages=input_messages)
    opt_prompt = optimizer.optimize_prompt(raw_prompt, deduplicate=True)

    formatted = opt_prompt.formatted_messages
    # Deduplication check
    assert len(formatted) == 6

    # Priority check: System (1) -> Developer (2) -> Memory (3) -> Workspace (4) -> Assistant (5) -> User (6)
    roles = [msg.role for msg in formatted]
    assert roles == [
        PromptRole.SYSTEM,
        PromptRole.DEVELOPER,
        PromptRole.MEMORY,
        PromptRole.WORKSPACE,
        PromptRole.ASSISTANT,
        PromptRole.USER,
    ]


def test_prompt_optimizer_large_prompt_trimming():
    """Test PromptOptimizer trims lower-priority messages when token limit is exceeded."""
    optimizer = TokenEstimator()
    prompt_optimizer = PromptOptimizer(token_estimator=optimizer)

    messages = [
        PromptMessage(role=PromptRole.SYSTEM, content="System prompt"),
        PromptMessage(role=PromptRole.DEVELOPER, content="Developer prompt"),
        PromptMessage(role=PromptRole.WORKSPACE, content="Workspace details text " * 10),
        PromptMessage(role=PromptRole.ASSISTANT, content="Old chat turn " * 20),
        PromptMessage(role=PromptRole.USER, content="Current user query"),
    ]

    prompt = Prompt(formatted_messages=messages)

    # Set tight token limit that forces trimming old chat turns
    opt_prompt = prompt_optimizer.optimize_prompt(prompt, max_tokens=40)
    opt_roles = [m.role for m in opt_prompt.formatted_messages]

    # System and Developer should be preserved
    assert PromptRole.SYSTEM in opt_roles
    assert PromptRole.DEVELOPER in opt_roles
    assert opt_prompt.token_estimate <= 40 or len(opt_roles) <= 3


# ---------------------------------------------------------------------------
# Tests: DefaultPromptBuilder End-to-End Pipeline
# ---------------------------------------------------------------------------


def test_default_prompt_builder_full_pipeline():
    """Test full DefaultPromptBuilder integration sitting between ContextBuilder and AIProvider."""
    ctx_builder = DefaultContextBuilder()
    prompt_builder = DefaultPromptBuilder(base_system_prompt="You are Auralis assistant.")

    req = BrainRequest(
        request_id="req-pipeline-100",
        raw_text="List files in current folder",
        session_id="session-100",
    )

    ctx = ctx_builder.build_context(
        request=req,
        conversation_history=[
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
        memory_context={"long_term": "Prefers CLI"},
        workspace_context={"root": "/home/user/app"},
    )

    prompt = prompt_builder.build_prompt(ctx)

    assert isinstance(prompt, Prompt)
    assert "Auralis" in prompt.system_prompt
    assert prompt.user_prompt == "List files in current folder"
    assert len(prompt.formatted_messages) > 0
    assert prompt.token_estimate > 0

    # Ensure messages are sorted by priority order
    roles = [m.role for m in prompt.formatted_messages]
    for i in range(len(roles) - 1):
        p1 = ROLE_PRIORITY.get(roles[i], 99)
        p2 = ROLE_PRIORITY.get(roles[i + 1], 99)
        assert p1 <= p2


def test_edge_cases_empty_and_malformed_context():
    """Test prompt pipeline edge cases with empty or minimal context."""
    prompt_builder = DefaultPromptBuilder()
    empty_ctx = AIContext(request_id="req-empty")

    prompt = prompt_builder.build_prompt(empty_ctx)
    assert isinstance(prompt, Prompt)
    assert prompt.system_prompt != ""
    assert prompt.token_estimate > 0
