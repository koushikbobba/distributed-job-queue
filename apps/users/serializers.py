from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserDetailSerializer(serializers.ModelSerializer):
    """Public representation of a user profile."""

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "is_active", "created_at")
        read_only_fields = ("id", "email", "is_active", "created_at")


class UserRegisterSerializer(serializers.ModelSerializer):
    """Handles new user registration with strict password validation."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("id", "email", "password", "password_confirm", "first_name", "last_name")
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data: dict):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Authenticates email/password credentials and issues JWT token pair."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserDetailSerializer(read_only=True)

    def validate(self, attrs: dict) -> dict:
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This user account is inactive.")

        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserDetailSerializer(user).data,
        }


class LogoutSerializer(serializers.Serializer):
    """Blacklists the provided refresh token to invalidate the session."""

    refresh = serializers.CharField(required=True)

    def validate(self, attrs: dict) -> dict:
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception as exc:
            raise serializers.ValidationError({"refresh": "Invalid or expired token."}) from exc
