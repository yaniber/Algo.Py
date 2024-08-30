import pytest
import subprocess

def test_save_script():
    result = subprocess.run(["python", "scripts/save_script.py"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Please choose the data type to save:" in result.stdout