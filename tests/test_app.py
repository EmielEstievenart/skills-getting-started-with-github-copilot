from fastapi.testclient import TestClient
from src.app import app
import pytest

client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self):
        """Test that root path redirects to static/index.html"""
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 307
        assert resp.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that getting activities returns 200 OK"""
        resp = client.get("/activities")
        assert resp.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that activities response is a dictionary"""
        resp = client.get("/activities")
        data = resp.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        resp = client.get("/activities")
        data = resp.json()
        
        for activity_name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)
            assert isinstance(details["max_participants"], int)

    def test_specific_activities_exist(self):
        """Test that expected activities are present"""
        resp = client.get("/activities")
        data = resp.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Club",
            "Swimming Club"
        ]
        
        for activity in expected_activities:
            assert activity in data


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        activity = "Chess Club"
        email = "new-student@example.com"
        
        # Get initial participant count
        resp = client.get("/activities")
        initial_participants = resp.json()[activity]["participants"].copy()
        
        # Sign up
        resp = client.post(f"/activities/{activity}/signup?email={email}")
        assert resp.status_code == 200
        assert f"Signed up {email}" in resp.json()["message"]
        
        # Verify participant was added
        resp = client.get("/activities")
        new_participants = resp.json()[activity]["participants"]
        assert email in new_participants
        assert len(new_participants) == len(initial_participants) + 1
        
        # Cleanup
        client.delete(f"/activities/{activity}/participants?email={email}")

    def test_signup_nonexistent_activity_returns_404(self):
        """Test that signing up for non-existent activity returns 404"""
        resp = client.post("/activities/Nonexistent Club/signup?email=test@example.com")
        assert resp.status_code == 404
        assert "Activity not found" in resp.json()["detail"]

    def test_signup_duplicate_returns_400(self):
        """Test that signing up twice with same email returns 400"""
        activity = "Programming Class"
        email = "duplicate-test@example.com"
        
        # First signup
        resp = client.post(f"/activities/{activity}/signup?email={email}")
        assert resp.status_code == 200
        
        # Second signup (duplicate)
        resp = client.post(f"/activities/{activity}/signup?email={email}")
        assert resp.status_code == 400
        assert "already signed up" in resp.json()["detail"]
        
        # Cleanup
        client.delete(f"/activities/{activity}/participants?email={email}")

    def test_signup_existing_participant_returns_400(self):
        """Test that signing up with an existing participant email returns 400"""
        # Get an existing participant
        resp = client.get("/activities")
        chess_club = resp.json()["Chess Club"]
        existing_email = chess_club["participants"][0]
        
        # Try to sign up again
        resp = client.post(f"/activities/Chess Club/signup?email={existing_email}")
        assert resp.status_code == 400
        assert "already signed up" in resp.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_success(self):
        """Test successful unregister from an activity"""
        activity = "Soccer Club"
        email = "unregister-test@example.com"
        
        # First sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Verify signup
        resp = client.get("/activities")
        assert email in resp.json()[activity]["participants"]
        
        # Unregister
        resp = client.delete(f"/activities/{activity}/participants?email={email}")
        assert resp.status_code == 200
        assert f"Unregistered {email}" in resp.json()["message"]
        
        # Verify removal
        resp = client.get("/activities")
        assert email not in resp.json()[activity]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self):
        """Test that unregistering from non-existent activity returns 404"""
        resp = client.delete("/activities/Fake Club/participants?email=test@example.com")
        assert resp.status_code == 404
        assert "Activity not found" in resp.json()["detail"]

    def test_unregister_missing_participant_returns_404(self):
        """Test that unregistering a non-participant returns 404"""
        activity = "Programming Class"
        missing = "not-in-list@example.com"
        
        resp = client.delete(f"/activities/{activity}/participants?email={missing}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Participant not found in this activity"

    def test_signup_and_unregister_cycle(self):
        """Test complete signup and unregister cycle"""
        activity = "Chess Club"
        email = "cycle-test@example.com"
        
        # Ensure email not present initially
        resp = client.get("/activities")
        assert resp.status_code == 200
        data = resp.json()
        assert email not in data[activity]["participants"]
        
        # Sign up
        resp = client.post(f"/activities/{activity}/signup?email={email}")
        assert resp.status_code == 200
        assert f"Signed up {email}" in resp.json().get("message", "")
        
        # Now email should be present
        resp = client.get("/activities")
        data = resp.json()
        assert email in data[activity]["participants"]
        
        # Unregister
        resp = client.delete(f"/activities/{activity}/participants?email={email}")
        assert resp.status_code == 200
        assert f"Unregistered {email}" in resp.json().get("message", "")
        
        # Ensure email is removed
        resp = client.get("/activities")
        data = resp.json()
        assert email not in data[activity]["participants"]


class TestMultipleOperations:
    """Tests for multiple operations and edge cases"""

    def test_multiple_signups_different_activities(self):
        """Test that a user can sign up for multiple activities"""
        email = "multi-activity@example.com"
        activities = ["Chess Club", "Programming Class", "Art Club"]
        
        # Sign up for multiple activities
        for activity in activities:
            resp = client.post(f"/activities/{activity}/signup?email={email}")
            assert resp.status_code == 200
        
        # Verify all signups
        resp = client.get("/activities")
        data = resp.json()
        for activity in activities:
            assert email in data[activity]["participants"]
        
        # Cleanup
        for activity in activities:
            client.delete(f"/activities/{activity}/participants?email={email}")

    def test_participant_count_accuracy(self):
        """Test that participant counts are accurate"""
        activity = "Drama Club"
        email = "count-test@example.com"
        
        # Get initial count
        resp = client.get("/activities")
        initial_count = len(resp.json()[activity]["participants"])
        
        # Add participant
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check count increased
        resp = client.get("/activities")
        new_count = len(resp.json()[activity]["participants"])
        assert new_count == initial_count + 1
        
        # Remove participant
        client.delete(f"/activities/{activity}/participants?email={email}")
        
        # Check count back to original
        resp = client.get("/activities")
        final_count = len(resp.json()[activity]["participants"])
        assert final_count == initial_count
