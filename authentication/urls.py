from django.urls import path
from .auth import (
    RegisterView,
    LoginView,
    CustomTokenRefreshView,
    ValidateTokenView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetView,
    EmailVerificationView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('token/validate/', ValidateTokenView.as_view(), name='validate_token'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetView.as_view(), name='password_reset_confirm'),
    path('email/verify/', EmailVerificationView.as_view(), name='email_verify'),
]
