from django.urls import path
from .views import (
    CustomTokenRefreshView,
    LoginView,
    LogoutView,
    RegisterView,
    UserProfileView,
)

app_name = "users"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", UserProfileView.as_view(), name="user-profile"),
]
