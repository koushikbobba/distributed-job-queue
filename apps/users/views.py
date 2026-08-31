from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    LogoutSerializer,
    UserDetailSerializer,
    UserLoginSerializer,
    UserRegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    Register a new user account.
    Returns the created user's public profile upon success.
    """

    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="User Registration",
        description="Creates a new user profile with email and password.",
        responses={
            201: UserDetailSerializer,
            400: OpenApiResponse(description="Validation error (e.g. email already exists or weak password)"),
        },
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserDetailSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Authenticate user credentials and issue a JSON Web Token (JWT) pair.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = UserLoginSerializer

    @extend_schema(
        summary="User Login",
        description="Authenticates email and password, returning an access token and refresh token.",
        request=UserLoginSerializer,
        responses={
            200: UserLoginSerializer,
            400: OpenApiResponse(description="Invalid credentials or inactive account"),
        },
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    """
    Refreshes an expired access token using a valid refresh token.
    """

    @extend_schema(
        summary="Refresh JWT Access Token",
        description="Submit a valid refresh token to obtain a new access token.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    """
    Blacklist the refresh token to immediately revoke the session.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(
        summary="User Logout",
        description="Revokes and blacklists the refresh token.",
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(description="Token successfully blacklisted"),
            400: OpenApiResponse(description="Invalid token"),
        },
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's profile.
    """

    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Current User Profile",
        description="Returns details for the currently authenticated user based on JWT token.",
        responses={200: UserDetailSerializer},
    )
    def get_object(self):
        return self.request.user
