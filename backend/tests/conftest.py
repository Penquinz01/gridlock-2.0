"""
Pytest configuration — ensures models and DB are loaded before tests.
"""

import pytest
from app.ml import load_models, models_loaded
from app.database import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_app():
    """Load models and init DB once for the entire test session."""
    if not models_loaded():
        load_models()
    init_db()
