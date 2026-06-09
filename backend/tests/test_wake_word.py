"""
Unit tests for the wake word detection module.
"""

import pytest
from voice_engine.wake_word import detect_wake_word, WAKE_PHRASES


# ---------------------------------------------------------------------------
# Basic activation tests — one per supported wake phrase
# ---------------------------------------------------------------------------

class TestWakeWordActivation:
    """Verify that every supported wake phrase triggers activation."""

    def test_hey_auralis(self):
        result = detect_wake_word("hey auralis open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_hi_auralis(self):
        result = detect_wake_word("hi auralis play music")
        assert result["activated"] is True
        assert result["cleaned_command"] == "play music"

    def test_hello_auralis(self):
        result = detect_wake_word("hello auralis what time is it")
        assert result["activated"] is True
        assert result["cleaned_command"] == "what time is it"

    def test_auralis_bare(self):
        result = detect_wake_word("auralis show files")
        assert result["activated"] is True
        assert result["cleaned_command"] == "show files"


# ---------------------------------------------------------------------------
# Non-activation tests
# ---------------------------------------------------------------------------

class TestNoActivation:
    """Verify that commands without a wake phrase are rejected."""

    def test_plain_command(self):
        result = detect_wake_word("open downloads")
        assert result["activated"] is False
        assert result["cleaned_command"] == ""

    def test_wake_word_in_middle(self):
        """Wake phrase must be at the start, not embedded in the command."""
        result = detect_wake_word("please hey auralis open files")
        assert result["activated"] is False
        assert result["cleaned_command"] == ""

    def test_similar_word(self):
        result = detect_wake_word("aurora open files")
        assert result["activated"] is False
        assert result["cleaned_command"] == ""


# ---------------------------------------------------------------------------
# Case-insensitivity
# ---------------------------------------------------------------------------

class TestCaseInsensitivity:
    """Confirm detection works regardless of letter casing."""

    def test_uppercase(self):
        result = detect_wake_word("HEY AURALIS open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_mixed_case(self):
        result = detect_wake_word("Hey Auralis Open Downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_title_case_hello(self):
        result = detect_wake_word("Hello Auralis delete temp")
        assert result["activated"] is True
        assert result["cleaned_command"] == "delete temp"


# ---------------------------------------------------------------------------
# Whitespace handling
# ---------------------------------------------------------------------------

class TestWhitespace:
    """Confirm leading, trailing, and internal whitespace is handled."""

    def test_leading_whitespace(self):
        result = detect_wake_word("   hey auralis open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_trailing_whitespace(self):
        result = detect_wake_word("hey auralis open downloads   ")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_both_sides_whitespace(self):
        result = detect_wake_word("  hey auralis open downloads  ")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_extra_internal_whitespace(self):
        """Extra spaces between wake phrase and command are collapsed."""
        result = detect_wake_word("hey auralis   open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_extra_spaces_within_wake_phrase(self):
        """Extra spaces inside the wake phrase itself are collapsed."""
        result = detect_wake_word("hey   auralis open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_extra_spaces_everywhere(self):
        result = detect_wake_word("  hello   auralis   open   documents  ")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open documents"


# ---------------------------------------------------------------------------
# Punctuation handling
# ---------------------------------------------------------------------------

class TestPunctuation:
    """Confirm punctuation between wake phrase and command is ignored."""

    def test_comma_after_wake_phrase(self):
        result = detect_wake_word("Hey Auralis, open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_period_after_wake_phrase(self):
        result = detect_wake_word("Hey Auralis. open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_exclamation_after_wake_phrase(self):
        result = detect_wake_word("Hey Auralis! open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_question_mark_in_command(self):
        result = detect_wake_word("Hey Auralis, what time is it?")
        assert result["activated"] is True
        assert result["cleaned_command"] == "what time is it"

    def test_semicolon_after_wake_phrase(self):
        result = detect_wake_word("Auralis; show files")
        assert result["activated"] is True
        assert result["cleaned_command"] == "show files"

    def test_multiple_punctuation_marks(self):
        result = detect_wake_word("Hey Auralis!! open downloads...")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_comma_no_space(self):
        result = detect_wake_word("Hey Auralis,open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_punctuation_only_no_activation(self):
        """Punctuation alone should not trigger activation."""
        result = detect_wake_word(",,, !!!")
        assert result["activated"] is False
        assert result["cleaned_command"] == ""


# ---------------------------------------------------------------------------
# User-provided examples
# ---------------------------------------------------------------------------

class TestUserExamples:
    """Exact examples from the requirements."""

    def test_hey_auralis_comma_open_downloads(self):
        result = detect_wake_word("Hey Auralis, open downloads")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open downloads"

    def test_hello_auralis_open_documents(self):
        result = detect_wake_word("Hello Auralis open documents")
        assert result["activated"] is True
        assert result["cleaned_command"] == "open documents"

    def test_auralis_create_folder_notes(self):
        result = detect_wake_word("Auralis create folder notes")
        assert result["activated"] is True
        assert result["cleaned_command"] == "create folder notes"


# ---------------------------------------------------------------------------
# Wake phrase only — no trailing command
# ---------------------------------------------------------------------------

class TestWakePhraseOnly:
    """Activation should succeed even without a trailing command."""

    def test_hey_auralis_only(self):
        result = detect_wake_word("hey auralis")
        assert result["activated"] is True
        assert result["cleaned_command"] == ""

    def test_auralis_only(self):
        result = detect_wake_word("auralis")
        assert result["activated"] is True
        assert result["cleaned_command"] == ""

    def test_hello_auralis_only_with_whitespace(self):
        result = detect_wake_word("  hello auralis  ")
        assert result["activated"] is True
        assert result["cleaned_command"] == ""

    def test_wake_phrase_with_trailing_comma(self):
        result = detect_wake_word("hey auralis,")
        assert result["activated"] is True
        assert result["cleaned_command"] == ""


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge-case inputs that should be handled gracefully."""

    def test_empty_string(self):
        result = detect_wake_word("")
        assert result["activated"] is False
        assert result["cleaned_command"] == ""

    def test_whitespace_only(self):
        result = detect_wake_word("     ")
        assert result["activated"] is False
        assert result["cleaned_command"] == ""

    def test_none_input(self):
        result = detect_wake_word(None)
        assert result["activated"] is False
        assert result["cleaned_command"] == ""

    def test_numeric_input(self):
        result = detect_wake_word(12345)
        assert result["activated"] is False
        assert result["cleaned_command"] == ""


# ---------------------------------------------------------------------------
# Return-value structure
# ---------------------------------------------------------------------------

class TestReturnStructure:
    """Ensure the returned dict always has the expected keys."""

    def test_keys_present_when_activated(self):
        result = detect_wake_word("hey auralis test")
        assert "activated" in result
        assert "cleaned_command" in result

    def test_keys_present_when_not_activated(self):
        result = detect_wake_word("random text")
        assert "activated" in result
        assert "cleaned_command" in result

    def test_activated_is_bool(self):
        result = detect_wake_word("hey auralis test")
        assert isinstance(result["activated"], bool)

    def test_cleaned_command_is_str(self):
        result = detect_wake_word("hey auralis test")
        assert isinstance(result["cleaned_command"], str)


# ---------------------------------------------------------------------------
# Parametrized sweep across all wake phrases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("phrase", WAKE_PHRASES)
class TestAllPhrasesParametrized:
    """Run the same assertions across every registered wake phrase."""

    def test_activation(self, phrase):
        result = detect_wake_word(f"{phrase} do something")
        assert result["activated"] is True
        assert result["cleaned_command"] == "do something"

    def test_activation_uppercase(self, phrase):
        result = detect_wake_word(f"{phrase.upper()} DO SOMETHING")
        assert result["activated"] is True
        assert result["cleaned_command"] == "do something"

    def test_phrase_only(self, phrase):
        result = detect_wake_word(phrase)
        assert result["activated"] is True
        assert result["cleaned_command"] == ""

    def test_phrase_with_comma(self, phrase):
        result = detect_wake_word(f"{phrase}, do something")
        assert result["activated"] is True
        assert result["cleaned_command"] == "do something"

