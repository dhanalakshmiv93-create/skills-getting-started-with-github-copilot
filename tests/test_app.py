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

    def test_signup_at_max_capacity_fails(self, client):
        """Test that signup fails when activity reaches maximum capacity."""
        activity_name = "Chess Club"  # max_participants: 12, starts with 2
        
        # Fill to capacity (add 10 more participants)
        for i in range(10):
            email = f"participant{i}@example.com"
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify at max
        activities_response = client.get("/activities")
        current_count = len(activities_response.json()[activity_name]["participants"])
        assert current_count == 12
        
        # Try to add one more - should fail
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "extra@example.com"}
        )
        assert response.status_code == 400
        assert "maximum capacity" in response.json()["detail"].lower()


class TestInputValidation:
    """Tests for input validation on email and parameters."""

    def test_signup_invalid_email_format(self, client):
        """Test that signup rejects invalid email formats."""
        activity_name = "Programming Class"
        invalid_emails = ["invalid", "no@domain", "@domain.com", "user@", ""]
        
        for email in invalid_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 422
            assert "invalid email" in response.json()["detail"].lower()

    def test_signup_missing_email_parameter(self, client):
        """Test that signup returns 422 when email parameter is missing."""
        activity_name = "Programming Class"
        response = client.post(f"/activities/{activity_name}/signup")
        assert response.status_code == 422

    def test_signup_empty_email(self, client):
        """Test that signup rejects empty email."""
        activity_name = "Programming Class"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": ""}
        )
        assert response.status_code == 422

    def test_unregister_invalid_email_format(self, client):
        """Test that unregister rejects invalid email formats."""
        activity_name = "Programming Class"
        invalid_emails = ["invalid", "no@domain", "@domain.com", "user@", ""]
        
        for email in invalid_emails:
            response = client.post(
                f"/activities/{activity_name}/unregister",
                params={"email": email}
            )
            assert response.status_code == 422
            assert "invalid email" in response.json()["detail"].lower()

    def test_unregister_missing_email_parameter(self, client):
        """Test that unregister returns 422 when email parameter is missing."""
        activity_name = "Programming Class"
        response = client.post(f"/activities/{activity_name}/unregister")
        assert response.status_code == 422

    def test_signup_case_sensitive_activity_name(self, client, sample_email):
        """Test that activity names are case sensitive."""
        # "chess club" should not match "Chess Club"
        response = client.post(
            "/activities/chess%20club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 404

    def test_signup_activity_name_with_spaces(self, client, sample_email):
        """Test that activity names with spaces work when URL encoded."""
        # "Gym Class" should work
        response = client.post(
            "/activities/Gym%20Class/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200
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


class TestErrorHandling:
    """Tests for error handling and HTTP method validation."""

    def test_get_on_signup_endpoint_returns_405(self, client, sample_email):
        """Test that GET on signup endpoint returns 405 Method Not Allowed."""
        response = client.get(
            "/activities/Chess%20Club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 405

    def test_put_on_signup_endpoint_returns_405(self, client, sample_email):
        """Test that PUT on signup endpoint returns 405 Method Not Allowed."""
        response = client.put(
            "/activities/Chess%20Club/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 405

    def test_delete_on_activities_endpoint_returns_405(self, client):
        """Test that DELETE on activities endpoint returns 405."""
        response = client.delete("/activities")
        assert response.status_code == 405

    def test_signup_response_format_consistency(self, client, sample_email):
        """Test that signup responses have consistent format."""
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": sample_email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert isinstance(data["message"], str)
        assert sample_email in data["message"]
        assert "Programming Class" in data["message"]

    def test_error_responses_have_detail_field(self, client):
        """Test that error responses include a detail field."""
        # Test 404 for non-existent activity
        response = client.post(
            "/activities/Nonexistent/signup",
            params={"email": "test@example.com"}
        )
        assert response.status_code == 404
        assert "detail" in response.json()
        assert isinstance(response.json()["detail"], str)


class TestDataConsistency:
    """Tests for data consistency and state management."""

    def test_activities_state_resets_between_tests(self, client):
        """Test that activities state is properly reset between tests."""
        # This test relies on the reset_activities fixture
        # Check that default participants are present
        response = client.get("/activities")
        activities = response.json()
        
        # Check a few known defaults
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "emma@mergington.edu" in activities["Programming Class"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 2  # Original count

    def test_signup_does_not_affect_other_activities(self, client, sample_email):
        """Test that signing up for one activity doesn't affect others."""
        activity_name = "Art Club"
        other_activity = "Drama Society"
        
        # Get initial counts
        response_before = client.get("/activities")
        before_counts = {
            name: len(data["participants"]) 
            for name, data in response_before.json().items()
        }
        
        # Sign up for one activity
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": sample_email}
        )
        
        # Check other activities unchanged
        response_after = client.get("/activities")
        after_counts = {
            name: len(data["participants"]) 
            for name, data in response_after.json().items()
        }
        
        for act_name in before_counts:
            if act_name != activity_name:
                assert before_counts[act_name] == after_counts[act_name]

    def test_default_participant_counts(self, client):
        """Test that activities have expected default participant counts."""
        response = client.get("/activities")
        activities = response.json()
        
        expected_counts = {
            "Chess Club": 2,
            "Programming Class": 2,
            "Gym Class": 2,
            "Basketball Team": 2,
            "Swimming Club": 2,
            "Art Club": 2,
            "Drama Society": 2,
            "Debate Team": 2,
            "Robotics Workshop": 2
        }
        
        for activity_name, expected_count in expected_counts.items():
            assert len(activities[activity_name]["participants"]) == expected_count


class TestStaticFiles:
    """Tests for static file serving."""

    def test_static_index_html_served(self, client):
        """Test that /static/index.html is accessible."""
        response = client.get("/static/index.html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_static_app_js_served(self, client):
        """Test that /static/app.js is accessible."""
        response = client.get("/static/app.js")
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]

    def test_static_styles_css_served(self, client):
        """Test that /static/styles.css is accessible."""
        response = client.get("/static/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]

    def test_static_nonexistent_file_returns_404(self, client):
        """Test that non-existent static files return 404."""
        response = client.get("/static/nonexistent.txt")
        assert response.status_code == 404
