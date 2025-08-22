from django.urls import path, include
# from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Create router and register viewsets
# router = DefaultRouter()
# router.register(r'users', UserViewSet, basename='user')

app_name = 'users'

urlpatterns = [
    # Include router URLs
    # path('', include(router.urls)),

    # Аутентификация
    path('auth/register/', UserViewSet.as_view(
        {'post': 'register'}
    ), name='user-register'),
    path('auth/login/', UserViewSet.as_view(
        {'post': 'login'}
    ), name='user-login'),
    path('auth/logout/', UserViewSet.as_view(
        {'post': 'logout'}
    ), name='user-logout'),

    # Управление профилем
    path('profile/me/', UserViewSet.as_view(
        {'get': 'me'}
    ), name='user-me'),
    path('profile/update/', UserViewSet.as_view(
        {'put': 'update_profile', 'patch': 'update_profile'}
    ), name='user-profile'),
    path('profile/change-password/', UserViewSet.as_view(
        {'post': 'change_password'}
    ), name='user-change-password'),
    path('profile/delete-account/', UserViewSet.as_view(
        {'post': 'delete_account'}
    ), name='user-delete-account'),
    path('users/', UserViewSet.as_view({
        'get': 'list'
    }), name='user-list'),
    path('users/<int:pk>/', UserViewSet.as_view({
        'get': 'retrieve'
    }), name='user-detail'),
]
