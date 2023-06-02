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


class IsActiveOrReadOnly(IsActive):
    """
    Разрешение на редактирование для авторизованного пользователя при условии,
    что он не забанен, в противном случае - только чтение.
    """
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view) or
            request.method in SAFE_METHODS
        )


class IsAdminOrReadOnly(IsActiveOrReadOnly):
    """Разрешение на редактирование только админу."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or (request.method in SAFE_METHODS)


class IsOwnerAdminOrReadOnly(IsAdminOrReadOnly):
    """
    Разрешение на редактирование хозяину своих записей (определяется в
    подклассе), админу - всех записей, в противном случае - чтение.
    """
    def has_object_permission(self, request, view, obj):
        return (
            self.is_owner(request, obj) or
            super().has_object_permission(request, view, obj)
        )

    def is_owner(self, request, obj):
        """Метод определяется в подклассе для обозначения владельца записи."""
        raise NotImplementedError


class IsAuthorAdminOrReadOnly(IsOwnerAdminOrReadOnly):
    """
    Разрешение на редактирование для автора рецепта, админа или только чтение.
    """
    def is_owner(self, request, obj):
        return obj.author == request.user


class IsFollowerAdminOrReadOnly(IsOwnerAdminOrReadOnly):
    """
    Разрешение на редактирование для подписчика, админа или только чтение.
    """
    def is_owner(self, request, obj):
        return obj.followed_by.filter(follower=request.user).first()
