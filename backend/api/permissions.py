from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticatedOrReadOnly

User = get_user_model()


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
        if not super().has_object_permission(request, view, obj):
            return False

        if request.user.is_staff:
            return True

        if isinstance(obj, User):
            if request.method == 'POST':
                return True
            if request.method == 'DELETE':
                return obj.followed_by.filter(follower=request.user).exists()

        if hasattr(obj, 'author'):
            return obj.author == request.user

        return False
