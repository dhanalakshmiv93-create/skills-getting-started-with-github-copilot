"""Comprehensive tests for the Mergington High School Activities API."""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_has_correct_structure(self, client):
        """Test that each activity has the required fields."""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_participants_are_strings(self, client):
        """Test that all participant entries are email strings."""
        response = client.get("/activities")
        activities = response.json()

        for activity_data in activities.values():
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_index_html(self, client):
        """Test that GET / redirects to the static HTML page."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful(self, client, sample_email):
        """Test that a student can successfully sign up for an activity."""
        activity_name = "Chess Club"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
        assert activity_name in data["message"]

    def test_signup_adds_participant_to_activity(self, client, sample_email):
        """Test that signup actually adds the participant to the activity."""
        activity_name = "Programming Class"
        
        # Get initial participants
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity_name]["participants"]
        
        # Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Check participants after signup
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        
        assert len(participants_after) == len(participants_before) + 1
        assert sample_email in participants_after

    def test_signup_duplicate_returns_400(self, client):
        """Test that signing up twice for the same activity returns 400 error."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client, sample_email):
        """Test that signing up for non-existent activity returns 404 error."""
        activity_name = "Nonexistent Club"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_with_url_encoded_email(self, client):
        """Test that signup works with URL-encoded email addresses."""
        activity_name = "Gym Class"
        email = "test+user@example.com"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200

    def test_signup_with_url_encoded_activity_name(self, client, sample_email):
        """Test that signup works with activities that have special characters."""
        # "Gym Class" is a real activity that could have spaces
        activity_name = "Gym Class"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_successful(self, client):
        """Test that a student can successfully unregister from an activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant_from_activity(self, client):
        """Test that unregister actually removes the participant from the activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify participant is there before
        response_before = client.get("/activities")
        assert email in response_before.json()[activity_name]["participants"]
        
        # Unregister
        client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Verify participant is gone after
        response_after = client.get("/activities")
        assert email not in response_after.json()[activity_name]["participants"]

    def test_unregister_nonexistent_participant_returns_404(self, client, sample_email):
        """Test that unregistering a participant not in activity returns 404 error."""
        activity_name = "Chess Club"
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": sample_email}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity_returns_404(self, client, sample_email):
        """Test that unregistering from non-existent activity returns 404 error."""
        activity_name = "Nonexistent Club"
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": sample_email}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_decreases_participant_count(self, client):
        """Test that unregister decreases the participant count."""
        activity_name = "Programming Class"
        email = "emma@mergington.edu"
        
        # Get count before
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])
        
        # Unregister
        client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Get count after
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        
        assert count_after == count_before - 1


class TestSignupUnregisterIntegration:
    """Integration tests for signup and unregister workflows."""

    def test_signup_then_unregister_workflow(self, client, sample_email):
        """Test complete workflow: sign up, verify, unregister, verify."""
        activity_name = "Debate Team"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        assert signup_response.status_code == 200
        
        # Verify in participants list
        get_response = client.get("/activities")
        assert sample_email in get_response.json()[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": sample_email}
        )
        assert unregister_response.status_code == 200
        
        # Verify not in participants list
        get_response_final = client.get("/activities")
        assert sample_email not in get_response_final.json()[activity_name]["participants"]

    def test_signup_after_unregister(self, client):
        """Test that a student can sign up again after unregistering."""
        activity_name = "Robotics Workshop"
        email = "sara@mergington.edu"
        
        # Unregister
        client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Sign up again should succeed
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify in list
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]
