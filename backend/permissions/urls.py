from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoleViewSet,
    UserRoleViewSet,
    RolePermissionViewSet,
    ResourceTypeViewSet
)

app_name = 'permissions'

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'user-roles', UserRoleViewSet, basename='user-role')
router.register(r'permissions', RolePermissionViewSet, basename='role-permission')
router.register(r'resource-types', ResourceTypeViewSet, basename='resource-types')

urlpatterns = [
    path('', include(router.urls)),
]
