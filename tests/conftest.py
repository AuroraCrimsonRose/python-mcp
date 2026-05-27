import pytest
from pathlib import Path

TEST_ROOT = Path(__file__).parent

@pytest.fixture
def workspace(tmp_path):
    return tmp_path