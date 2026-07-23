"""Tests for hardware detection error paths."""

import subprocess
from unittest.mock import patch

from llmlaunchpad.hardware import get_cpu_name, detect_gpus


def test_get_cpu_name_falls_back_on_timeout():
    """A hung CPU-name probe must degrade to a fallback string, not raise."""
    with patch('subprocess.check_output', side_effect=subprocess.TimeoutExpired('cmd', 5)):
        name = get_cpu_name()

    assert isinstance(name, str)
    assert name != ""


def test_get_cpu_name_falls_back_on_error():
    """Any probe error must degrade to a fallback string, not raise."""
    with patch('subprocess.check_output', side_effect=OSError("boom")):
        name = get_cpu_name()

    assert isinstance(name, str)
    assert name != ""


def test_detect_gpus_returns_list_without_gputil():
    """GPU detection must return a list even when no GPU backend is available."""
    gpus = detect_gpus()
    assert isinstance(gpus, list)
