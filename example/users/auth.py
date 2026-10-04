import jwt

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import UserMaster


class DynamicNavJWTAuthentication(BaseAuthentication):

    keyword = "Bearer"

    def authenticate(self, request):

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        parts = auth_header.split()

        if len(parts) != 2:
            raise AuthenticationFailed(
                "Invalid Authorization header."
            )

        if parts[0].lower() != self.keyword.lower():
            raise AuthenticationFailed(
                "Authorization header must use Bearer token."
            )

        token = parts[1]

        payload = self._decode_token(token)

        user = self._get_user(payload)

        if user is None:
            raise AuthenticationFailed(
                "User not found."
            )

        # UserMaster doesn't inherit Django AbstractUser,
        # so it may not have is_authenticated.
        if hasattr(user, "is_active") and not user.is_active:
            raise AuthenticationFailed(
                "User account is inactive."
            )

        return user, token

    def authenticate_header(self, request):
        return self.keyword

    def _decode_token(self, token):

        secret_key = getattr(
            settings,
            "JWT_SECRET_KEY",
            None,
        )

        algorithm = getattr(
            settings,
            "JWT_ALGORITHM",
            "HS256",
        )

        if not secret_key:
            raise AuthenticationFailed(
                "JWT_SECRET_KEY is not configured."
            )

        try:

            payload = jwt.decode(
                token,
                secret_key,
                algorithms=[algorithm],
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed(
                "Token has expired."
            )

        except jwt.InvalidTokenError:
            raise AuthenticationFailed(
                "Invalid token."
            )

    def _get_user(self, payload):

        user_id = payload.get("user_id")

        if user_id is None:
            raise AuthenticationFailed(
                "User ID is missing from token."
            )

        try:
            return UserMaster.objects.get(
                id=user_id
            )

        except UserMaster.DoesNotExist:
            return None
        