"""Pytest configuration and shared fixtures for FastAPI app tests."""

import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities


# Store the original activities state
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test."""
    # Import here to get fresh reference
    from src import app as app_module
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield
    # Cleanup after test
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))


@pytest.fixture
def client():
    """Provide a TestClient instance for making requests to the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_activity():
    """Provide sample activity data for testing."""
    return {
        "name": "Test Club",
        "details": {
            "description": "A test activity",
            "schedule": "Mondays, 3:00 PM - 4:00 PM",
            "max_participants": 10,
            "participants": ["alice@test.edu", "bob@test.edu"]
        }
    }


@pytest.fixture
def sample_email():
    """Provide a sample email for testing signup/unregister."""
    return "charlie@test.edu"
