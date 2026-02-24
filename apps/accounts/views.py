"""
Authentication and account management API views.

This module provides endpoints for user registration, login,
JWT handling, account activation, logout, and password reset
workflows for the Videoflix backend.
"""
import token
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.contrib.auth import authenticate, get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
User = get_user_model()

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
# =========================
# # REGISTER
# # =========================
# class RegisterView(APIView):
#     permission_classes = [AllowAny]
#     authentication_classes = []

#     def post(self, request):
#         serializer = RegisterSerializer(data=request.data)

#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         user = serializer.save()
#         user.is_active = False
#         user.save()

#         uid = urlsafe_base64_encode(force_bytes(user.pk))
#         token = default_token_generator.make_token(user)

#         activation_link = (
#         f"http://127.0.0.1:5500/pages/auth/activate.html"
#     f"?uid={uid}&token={token}"
# )

#         print("ACTIVATION LINK:", activation_link)   

#         send_mail(
#             subject="Activate your account",
#             message=f"Activate account: {activation_link}",
#             from_email="noreply@videoflix.com",
#             recipient_list=[user.email],
#             fail_silently=True,
#         )

#         return Response(
#             {"detail": "User registered successfully. Check your email."},
#             status=status.HTTP_201_CREATED,
#         )
class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        user.is_active = False
        user.save()

        # Generate uid + token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Link do FRONTENDU (zgodnie z projektem)
        activation_link = (
            f"http://127.0.0.1:5500/pages/auth/activate.html"
            f"?uid={uid}&token={token}"
        )

        # Render HTML template
        subject = "Activate your account"

        html_content = render_to_string(
            "emails/activate_account.html",
            {
                "activation_link": activation_link,
                "user": user,
            }
        )

        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email="noreply@videoflix.com",
            to=[user.email],
        )

        email.attach_alternative(html_content, "text/html")
        email.send()

        return Response(
            {"detail": "User registered successfully. Check your email."},
            status=status.HTTP_201_CREATED,
        )

# =========================
# LOGIN
# =========================
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "Account not activated"},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        response = Response(
            {
                "detail": "Login successful",
                "user": {
                    "id": user.id,
                    "email": user.email,
                },
            },
            status=status.HTTP_200_OK,
        )

        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            samesite="Lax",
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            samesite="Lax",
        )

        return response

# =========================
# ACTIVATE ACCOUNT
# =========================
class ActivateAccountView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"message": "Invalid activation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"message": "Invalid or expired activation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = True
        user.save()

        return Response(
            {"message": "Account successfully activated!"},
            status=status.HTTP_200_OK,
        )

# =========================
# LOGOUT
# =========================
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = Response(
            {"detail": "Logout successful"},
            status=status.HTTP_200_OK,
        )

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response


# =========================
# REFRESH TOKEN
# =========================
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            new_access = refresh.access_token

            response = Response(
                {"detail": "Token refreshed"},
                status=status.HTTP_200_OK,
            )

            response.set_cookie(
                key="access_token",
                value=str(new_access),
                httponly=True,
                samesite="Lax",
            )

            return response

        except TokenError:
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


# =========================
# PASSWORD RESET
# =========================
class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"detail": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = f"http://localhost:8000/api/password_confirm/{uid}/{token}/"
            print("RESET LINK:", reset_link)

        except User.DoesNotExist:
            pass

        return Response(
            {"detail": "If account exists, reset email was sent."},
            status=status.HTTP_200_OK,
        )


class PasswordConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not new_password or not confirm_password:
            return Response(
                {"detail": "Both password fields are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {"detail": "Passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"detail": "Password successfully reset."},
            status=status.HTTP_200_OK,
        )
    

