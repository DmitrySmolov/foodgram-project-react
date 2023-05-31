from django.contrib.auth import get_user_model
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)

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
        if request.method in SAFE_METHODS:
            return super().has_permission(request, view)
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
            return super().has_permission(request, view)
        return (
            (request.user.is_staff or self.is_owner(request, obj)) and
            super().has_permission(request, view)
        )

    def is_owner(self, request, obj):
        """Метод определяется во вьюсетах для обозначения владельца записи."""
        raise NotImplementedError
