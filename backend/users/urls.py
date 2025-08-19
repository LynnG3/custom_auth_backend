from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='profile')

app_name = 'users'

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
