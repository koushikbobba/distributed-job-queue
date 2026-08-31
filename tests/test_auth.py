import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def _create_user(email="testuser@example.com", password="StrongPassword123!"):
        return User.objects.create_user(email=email, password=password)

    return _create_user


@pytest.mark.django_db
class TestUserAuthentication:
    def test_user_registration_success(self, api_client):
        url = reverse("users:register")
        payload = {
            "email": "newuser@example.com",
            "password": "ValidPassword123!",
            "password_confirm": "ValidPassword123!",
            "first_name": "John",
            "last_name": "Doe",
        }
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["email"] == "newuser@example.com"
        assert "password" not in response.data
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_user_registration_password_mismatch(self, api_client):
        url = reverse("users:register")
        payload = {
            "email": "mismatch@example.com",
            "password": "Password123!",
            "password_confirm": "DifferentPassword123!",
        }
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.data

    def test_user_login_success(self, api_client, create_user):
        user = create_user(email="loginuser@example.com", password="SecretPassword123!")
        url = reverse("users:login")
        payload = {"email": "loginuser@example.com", "password": "SecretPassword123!"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == user.email

    def test_user_login_invalid_credentials(self, api_client, create_user):
        create_user(email="loginuser@example.com", password="SecretPassword123!")
        url = reverse("users:login")
        payload = {"email": "loginuser@example.com", "password": "WrongPassword"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_authenticated_user_profile(self, api_client, create_user):
        user = create_user(email="profile@example.com", password="Password123!")
        login_url = reverse("users:login")
        login_resp = api_client.post(login_url, {"email": user.email, "password": "Password123!"})
        token = login_resp.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        profile_url = reverse("users:user-profile")
        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email

    def test_token_refresh(self, api_client, create_user):
        user = create_user(email="refresh@example.com", password="Password123!")
        login_url = reverse("users:login")
        login_resp = api_client.post(login_url, {"email": user.email, "password": "Password123!"})
        refresh_token = login_resp.data["refresh"]

        refresh_url = reverse("users:token-refresh")
        response = api_client.post(refresh_url, {"refresh": refresh_token})

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_logout_blacklists_refresh_token(self, api_client, create_user):
        user = create_user(email="logout@example.com", password="Password123!")
        login_url = reverse("users:login")
        login_resp = api_client.post(login_url, {"email": user.email, "password": "Password123!"})
        access_token = login_resp.data["access"]
        refresh_token = login_resp.data["refresh"]

        # Logout with auth header
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_url = reverse("users:logout")
        response = api_client.post(logout_url, {"refresh": refresh_token})
        assert response.status_code == status.HTTP_200_OK

        # Try to use blacklisted refresh token again -> should fail
        refresh_url = reverse("users:token-refresh")
        refresh_resp = api_client.post(refresh_url, {"refresh": refresh_token})
        assert refresh_resp.status_code == status.HTTP_401_UNAUTHORIZED
