# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # User profile management
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/comprehensive/', views.ComprehensiveUserView.as_view(), name='comprehensive-profile'),
    path('profile/basic/', views.UpdateBasicUserInfoView.as_view(), name='update-basic-info'),
    
    # Avatar management
    path('avatar/', views.UserAvatarView.as_view(), name='avatar'),
    
    # Document management
    path('documents/', views.UserDocumentListView.as_view(), name='documents'),
    path('documents/<int:pk>/', views.UserDocumentDetailView.as_view(), name='document-detail'),
    
    # Settings
    path('notifications/', views.NotificationSettingsView.as_view(), name='notification-settings'),
    path('preferences/', views.UserPreferencesView.as_view(), name='preferences'),
    
    # Activity and logs
    path('activity/', views.UserActivityLogView.as_view(), name='activity-log'),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    
    # Subscription
    path('subscription/', views.UserSubscriptionView.as_view(), name='subscription'),
    
    # Team invitations
    path('invitations/', views.TeamInvitationListView.as_view(), name='invitations'),
    path('invitations/received/', views.ReceivedInvitationsView.as_view(), name='received-invitations'),
    path('invitations/<int:pk>/', views.TeamInvitationDetailView.as_view(), name='invitation-detail'),
    path('invitations/<str:token>/accept/', views.accept_invitation, name='accept-invitation'),
    path('invitations/<str:token>/decline/', views.decline_invitation, name='decline-invitation'),
    
    # Account management
    path('deactivate/', views.deactivate_account, name='deactivate-account'),
    path('export/', views.export_user_data, name='export-data'),
]
