from django.contrib.auth import get_user_model
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly, SAFE_METHODS
)

User = get_user_model()


class IsActive(IsAuthenticated):
    """
    Разрешение только авторизованному пользователю, если он не забанен.
    """
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view) and
            request.user.is_active
        )


class IsActiveOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Разрешение на редактирование для авторизованного пользователя при условии,
    что он не забанен, в противном случае - только чтение.
    """
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view) and
            request.user.is_active
        )


class IsOwnerAdminOrReadOnly(IsActiveOrReadOnly):
    """
    Разрешение на редактирование своих записей подписок, рецептов, избранного,
    списка покупок, для админа - всех записей, в противном случае - чтение.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return (
                request.user and
                request.user.is_authenticated and
                request.user.is_active
            )
        if request.user.is_staff:
            return True
        return self.is_owner(request, obj)

    def is_owner(self, request, obj):
        """Метод определяется во вьюсетах для обозначения владельца записи."""
        raise NotImplementedError
