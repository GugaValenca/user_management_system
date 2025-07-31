from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('activity-logs/', views.UserActivityLogView.as_view(), name='activity_logs'),
    path('users/', views.AdminUserListView.as_view(), name='user_list'),
    path('stats/', views.user_stats, name='user_stats'),
]
