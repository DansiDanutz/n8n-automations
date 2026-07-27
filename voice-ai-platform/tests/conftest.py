import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


test_root = tempfile.mkdtemp(prefix="voice-platform-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{test_root}/voice.db"
os.environ["BOOTSTRAP_API_KEY"] = "test-bootstrap-key-that-is-at-least-32-characters"
os.environ["SECRET_KEY"] = "test-signing-key-that-is-at-least-32-characters"
os.environ["ELEVENLABS_API_KEY"] = "test-elevenlabs-key"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["CORS_ORIGINS"] = "https://voice.example"
sys.path.insert(0, str(Path(__file__).parents[1]))

from main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
