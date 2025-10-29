from fastapi.testclient import TestClient
import copy

from src.app import app, activities


client = TestClient(app)


def setup_function():
    # Make a deep copy of activities to restore after each test
    global _activities_backup
    _activities_backup = copy.deepcopy(activities)


def teardown_function():
    # Restore activities
    activities.clear()
    activities.update(copy.deepcopy(_activities_backup))


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data


def test_signup_and_unregister_flow():
    activity_name = "Basketball Club"
    email = "teststudent@example.com"

    # Ensure not already present
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity_name]["participants"]

    # Sign up
    resp = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert resp.status_code == 200
    assert f"Signed up {email}" in resp.json().get("message", "")

    # Confirm present
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email in resp.json()[activity_name]["participants"]

    # Duplicate signup should fail with 400
    resp = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert resp.status_code == 400

    # Unregister
    resp = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert resp.status_code == 200
    assert f"Unregistered {email}" in resp.json().get("message", "")

    # Confirm removed
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity_name]["participants"]
from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities before/after each test to avoid cross-test pollution."""
    original = deepcopy(app_module.activities)
    yield
    app_module.activities = original


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # Basic sanity: should contain some known activities
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"], dict)


def test_signup_and_unregister_flow(client):
    activity = "Chess Club"
    email = "test_student@example.com"

    # Ensure email not present initially
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity]["participants"]

    # Sign up
    signup = client.post(f"/activities/{quote(activity)}/signup?email={email}")
    assert signup.status_code == 200
    assert email in client.get("/activities").json()[activity]["participants"]

    # Signing up again should fail (already signed up)
    signup_again = client.post(f"/activities/{quote(activity)}/signup?email={email}")
    assert signup_again.status_code == 400

    # Unregister
    delete = client.delete(f"/activities/{quote(activity)}/unregister?email={email}")
    assert delete.status_code == 200
    assert email not in client.get("/activities").json()[activity]["participants"]


def test_unregister_nonexistent_student(client):
    activity = "Programming Class"
    email = "not_registered@example.com"

    # Ensure student is not registered
    assert email not in client.get("/activities").json()[activity]["participants"]

    # Attempt to unregister should return 404
    resp = client.delete(f"/activities/{quote(activity)}/unregister?email={email}")
    assert resp.status_code == 404
