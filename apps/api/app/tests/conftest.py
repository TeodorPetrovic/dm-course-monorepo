import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def client():
    tmp = Path(tempfile.mkdtemp(prefix="dmml-"))
    os.environ["DM_MODELS_DIR"] = str(tmp / "models"); (tmp / "models").mkdir()
    os.environ["DM_LIVE_EVENTS"] = str(tmp / "live_events.csv")
    os.environ.pop("AI_PROVIDER", None); os.environ.pop("AI_EXTERNAL_API_KEY", None)
    from fastapi.testclient import TestClient
    from app.api.routes import reset_services
    from app.services import store
    store.set_store(None); reset_services()
    from app.main import app
    return TestClient(app)
