# authentication/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # Email verification
    path('verify-email/<str:token>/', views.verify_email, name='verify-email'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend-verification'),
    
    # Password management
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # User profile
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('stats/', views.user_stats, name='user-stats'),
    
    # Session management
    path('sessions/', views.UserSessionsView.as_view(), name='user-sessions'),
    path('sessions/<int:session_id>/revoke/', views.revoke_session, name='revoke-session'),
]
