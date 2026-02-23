from django.urls import path
from .views import ActivateAccountView, LogoutView, PasswordConfirmView, PasswordResetView, RefreshTokenView, RegisterView, LoginView
from .views import ActivateAccountView
urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("activate/<uidb64>/<path:token>/", ActivateAccountView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("token/refresh/", RefreshTokenView.as_view()),
    path("password_reset/", PasswordResetView.as_view()),
    path("password_confirm/<uidb64>/<token>/", PasswordConfirmView.as_view()),
] 