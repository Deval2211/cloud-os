"""
Integration tests for authentication and workspace endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

from main import app, SessionLocal
from models import Base, User
from auth.db import get_db_session
from config import settings


# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
app.dependency_overrides[get_db_session] = override_get_db
client = TestClient(app)


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_health_check(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_readiness_check(self):
        """Test readiness endpoint"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ready", "not_ready"]

    def test_github_auth_url(self):
        """Test getting GitHub OAuth URL"""
        response = client.get("/api/v1/auth/github")
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "state" in data
        assert "github.com" in data["url"]

    @patch("routes.auth.GitHubOAuthService.exchange_code_for_token")
    @patch("routes.auth.GitHubOAuthService.get_user_info")
    def test_github_callback_new_user(self, mock_get_user, mock_exchange):
        """Test GitHub OAuth callback for new user"""
        # Mock GitHub API responses
        mock_exchange.return_value = "fake_access_token"
        mock_get_user.return_value = {
            "github_id": "12345",
            "username": "testuser",
            "email": "test@example.com",
            "display_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
        }

        response = client.post(
            "/api/v1/auth/github/callback",
            json={"code": "test_code", "state": "test_state"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"

    @patch("routes.auth.GitHubOAuthService.exchange_code_for_token")
    def test_github_callback_failed_exchange(self, mock_exchange):
        """Test GitHub callback when code exchange fails"""
        mock_exchange.return_value = None

        response = client.post(
            "/api/v1/auth/github/callback",
            json={"code": "invalid_code", "state": "test_state"},
        )

        assert response.status_code == 400

    def test_get_current_user_unauthorized(self):
        """Test getting current user without auth"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_logout_unauthorized(self):
        """Test logout without auth"""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    def test_refresh_token_not_found(self):
        """Test token refresh without refresh token"""
        response = client.post("/api/v1/auth/refresh")
        assert response.status_code == 401


class TestWorkspaceEndpoints:
    """Test workspace endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test user and auth"""
        db = TestingSessionLocal()

        # Create test user
        user = User(
            id="test-user-123",
            github_id="github-123",
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            is_active=True,
            is_admin=False,
        )
        db.add(user)
        db.commit()

        self.user = user
        self.user_id = user.id
        yield
        db.close()

    def get_auth_token(self):
        """Generate test auth token"""
        from auth.utils import create_access_token

        return create_access_token({"sub": self.user_id, "email": "test@example.com"})

    def test_create_workspace_unauthorized(self):
        """Test creating workspace without auth"""
        response = client.post(
            "/api/v1/workspaces",
            json={"name": "Test Workspace"},
        )
        assert response.status_code == 401

    def test_create_workspace(self):
        """Test creating workspace"""
        token = self.get_auth_token()
        response = client.post(
            "/api/v1/workspaces",
            json={"name": "My Workspace", "description": "Test workspace"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Workspace"
        assert data["description"] == "Test workspace"
        assert data["owner_id"] == self.user_id

    def test_get_workspaces(self):
        """Test listing workspaces"""
        token = self.get_auth_token()

        # Create a workspace
        client.post(
            "/api/v1/workspaces",
            json={"name": "Workspace 1"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # List workspaces
        response = client.get(
            "/api/v1/workspaces",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Workspace 1"

    def test_get_workspace_by_id(self):
        """Test getting specific workspace"""
        token = self.get_auth_token()

        # Create a workspace
        create_response = client.post(
            "/api/v1/workspaces",
            json={"name": "Test Workspace"},
            headers={"Authorization": f"Bearer {token}"},
        )
        workspace_id = create_response.json()["id"]

        # Get the workspace
        response = client.get(
            f"/api/v1/workspaces/{workspace_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workspace_id
        assert data["name"] == "Test Workspace"

    def test_get_nonexistent_workspace(self):
        """Test getting non-existent workspace"""
        token = self.get_auth_token()
        response = client.get(
            "/api/v1/workspaces/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_update_workspace(self):
        """Test updating workspace"""
        token = self.get_auth_token()

        # Create a workspace
        create_response = client.post(
            "/api/v1/workspaces",
            json={"name": "Original Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        workspace_id = create_response.json()["id"]

        # Update the workspace
        response = client.patch(
            f"/api/v1/workspaces/{workspace_id}",
            json={"name": "Updated Name", "description": "New description"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    def test_delete_workspace(self):
        """Test deleting workspace"""
        token = self.get_auth_token()

        # Create a workspace
        create_response = client.post(
            "/api/v1/workspaces",
            json={"name": "Workspace to Delete"},
            headers={"Authorization": f"Bearer {token}"},
        )
        workspace_id = create_response.json()["id"]

        # Delete the workspace
        response = client.delete(
            f"/api/v1/workspaces/{workspace_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Workspace deleted successfully"

        # Verify workspace is deleted
        get_response = client.get(
            f"/api/v1/workspaces/{workspace_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    def test_workspace_ownership(self):
        """Test workspace ownership protection"""
        token1 = self.get_auth_token()

        # Create a workspace as user 1
        create_response = client.post(
            "/api/v1/workspaces",
            json={"name": "User 1 Workspace"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        workspace_id = create_response.json()["id"]

        # Create another test user
        db = TestingSessionLocal()
        user2 = User(
            id="test-user-456",
            github_id="github-456",
            username="testuser2",
            email="test2@example.com",
            display_name="Test User 2",
            is_active=True,
            is_admin=False,
        )
        db.add(user2)
        db.commit()
        db.close()

        # Try to delete workspace as user 2
        token2 = create_access_token({"sub": user2.id, "email": "test2@example.com"})
        response = client.delete(
            f"/api/v1/workspaces/{workspace_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Access denied"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
