from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

app_name = 'users'

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    # REST framework browsable API
    path('auth/', include('rest_framework.urls')),
    # Дополнительные endpoints для аутентификации
    path('auth/register/', UserViewSet.as_view(
        {'post': 'register'}
    ), name='user-register'),
    path('auth/login/', UserViewSet.as_view(
        {'post': 'login'}
    ), name='user-login'),
    path('auth/logout/', UserViewSet.as_view(
        {'post': 'logout'}
    ), name='user-logout'),
    path('auth/me/', UserViewSet.as_view(
        {'get': 'me'}
    ), name='user-me'),
    path('auth/profile/', UserViewSet.as_view(
        {'put': 'update_profile', 'patch': 'update_profile'}
    ), name='user-profile'),
    path('auth/change-password/', UserViewSet.as_view(
        {'post': 'change_password'}
    ), name='user-change-password'),
    path('auth/delete-account/', UserViewSet.as_view(
        {'post': 'delete_account'}
    ), name='user-delete-account'),
]
