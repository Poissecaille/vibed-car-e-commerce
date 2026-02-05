"""Tests for user module."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from ninja_jwt.tokens import RefreshToken

User = get_user_model()


class TestUserModel(TestCase):
    """Tests for User model."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.role, "CLIENT")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.assertEqual(user.email, "admin@example.com")
        self.assertEqual(user.role, "ADMIN")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_full_name(self):
        """Test user full_name property."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )
        self.assertEqual(user.full_name, "John Doe")

    def test_user_soft_delete(self):
        """Test user soft delete."""
        user = User.objects.create_user(
            email="delete@example.com",
            password="testpass123"
        )
        user_id = user.id
        user.delete()

        # Should not appear in normal queryset
        self.assertFalse(User.objects.filter(id=user_id).exists())

        # Should appear in all_objects
        self.assertTrue(User.all_objects.filter(id=user_id).exists())

        # Check soft delete fields
        deleted_user = User.all_objects.get(id=user_id)
        self.assertTrue(deleted_user.is_deleted)
        self.assertIsNotNone(deleted_user.deleted_at)


class TestUserAPI(TestCase):
    """Tests for User API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.password = "TestPass123!"
        self.user = User.objects.create_user(
            email="user@test.com",
            password=self.password,
            first_name="Test",
            last_name="User",
        )
        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}

    def test_register_user(self):
        """Test user registration."""
        response = self.client.post(
            "/api/v1/users/register",
            data={
                "email": "newuser@example.com",
                "password": "testpass123",
                "first_name": "New",
                "last_name": "User"
            },
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["email"], "newuser@example.com")
        self.assertNotIn("password", data)

    def test_get_current_user(self):
        """Test getting current user details."""
        response = self.client.get(
            "/api/v1/users/me",
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.user.email)

    def test_update_current_user(self):
        """Test updating current user."""
        response = self.client.patch(
            "/api/v1/users/me",
            data={"first_name": "Updated"},
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["first_name"], "Updated")

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoint."""
        response = self.client.get("/api/v1/users/me")
        self.assertEqual(response.status_code, 401)
