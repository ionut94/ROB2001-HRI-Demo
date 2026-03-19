"""Tests for src/tts.py — subprocess-safe TTS wrapper.

Note: We test that speak_pyttsx3_safe generates and runs a valid subprocess
      script. We don't test actual audio output (hardware-dependent).
"""

import subprocess
import sys
from unittest.mock import patch, MagicMock

import pytest

from src.tts import speak_pyttsx3_safe


class TestSpeakPyttsx3Safe:
    @patch("src.tts.subprocess.run")
    def test_calls_subprocess(self, mock_run):
        speak_pyttsx3_safe("Hello")
        mock_run.assert_called_once()

    @patch("src.tts.subprocess.run")
    def test_uses_sys_executable(self, mock_run):
        speak_pyttsx3_safe("Hello")
        call_args = mock_run.call_args
        assert call_args[0][0][0] == sys.executable

    @patch("src.tts.subprocess.run")
    def test_passes_c_flag(self, mock_run):
        speak_pyttsx3_safe("Hello")
        call_args = mock_run.call_args
        assert call_args[0][0][1] == "-c"

    @patch("src.tts.subprocess.run")
    def test_script_contains_text(self, mock_run):
        speak_pyttsx3_safe("Test message")
        call_args = mock_run.call_args
        script = call_args[0][0][2]
        assert "Test message" in script

    @patch("src.tts.subprocess.run")
    def test_script_contains_rate(self, mock_run):
        speak_pyttsx3_safe("Hello", rate=200)
        call_args = mock_run.call_args
        script = call_args[0][0][2]
        assert "200" in script

    @patch("src.tts.subprocess.run")
    def test_script_contains_language(self, mock_run):
        speak_pyttsx3_safe("Bonjour", language="fr")
        call_args = mock_run.call_args
        script = call_args[0][0][2]
        assert "'fr'" in script

    @patch("src.tts.subprocess.run")
    def test_timeout_is_set(self, mock_run):
        speak_pyttsx3_safe("Hello")
        call_args = mock_run.call_args
        assert call_args[1]["timeout"] == 30

    @patch("src.tts.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="", timeout=30))
    def test_handles_timeout_gracefully(self, mock_run, capsys):
        speak_pyttsx3_safe("Hello")  # should not raise
        captured = capsys.readouterr()
        assert "timed out" in captured.out.lower()

    @patch("src.tts.subprocess.run")
    def test_special_characters_in_text(self, mock_run):
        """Ensure quotes and special chars don't break the generated script."""
        speak_pyttsx3_safe("It's a \"test\" with special chars: <>&")
        mock_run.assert_called_once()  # didn't crash
        script = mock_run.call_args[0][0][2]
        assert "pyttsx3" in script

    @patch("src.tts.subprocess.run")
    def test_generated_script_is_valid_python(self, mock_run):
        """The generated script should be parseable Python."""
        speak_pyttsx3_safe("Hello world", rate=175, language="en")
        script = mock_run.call_args[0][0][2]
        # compile() will raise SyntaxError if the script is invalid
        compile(script, "<test>", "exec")
