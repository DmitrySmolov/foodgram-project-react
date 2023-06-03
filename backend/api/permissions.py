from django.contrib.auth import get_user_model
from rest_framework.permissions import (BasePermission, SAFE_METHODS)

User = get_user_model()


class IsActive(BasePermission):
    """
    Разрешение только авторизованному пользователю, если он не забанен.
    """
    def has_permission(self, request, _):
        return (
            request.user.is_authenticated and request.user.is_active
        )


class IsActiveOrReadOnly(BasePermission):
    """
    Разрешение на редактирование для авторизованного пользователя при условии,
    что он не забанен, в противном случае - только чтение.
    """
    def has_permission(self, request, _):
        return (
            request.method in SAFE_METHODS or
            request.user.is_authenticated and request.user.is_active
        )


class IsAdminOrReadOnly(BasePermission):
    """Разрешение на редактирование только админу."""
    def has_permission(self, request, _):
        return (
            request.method in SAFE_METHODS or
            request.user.is_authenticated and request.user.is_staff
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS or
            request.user.is_authenticated and request.user.is_staff
        )


class IsAuthorAdminOrReadOnly(BasePermission):
    """
    Разрешение на редактирование для автора рецепта, админа или только чтение.
    """
    def has_permission(self, request, _):
        return (
            request.method in SAFE_METHODS or
            request.user.is_authenticated and request.user.is_active
        )

    def has_object_permission(self, request, _, obj):
        return (
            request.method in SAFE_METHODS or
            request.user.is_authenticated and
            (obj.author == request.user or request.user.is_staff)
        )


class IsFollowerAdminOrReadOnly(BasePermission):
    """
    Разрешение на редактирование для подписчика, админа или только чтение.
    """
    def has_permission(self, request, _):
        return (
            request.method in SAFE_METHODS or
            request.user.is_authenticated and request.user.is_active
        )

    def has_object_permission(self, request, _, obj):
        return (
            request.method in SAFE_METHODS or
            request.user.is_authenticated and (
                obj.followed_by.filter(follower=request.user).exists() or
                request.user.is_staff
            )
        )
