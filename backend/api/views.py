from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from api.permissions import IsOwnerAdminOrReadOnly
from api.serializers import (
    UserSerializer, SubscriptionSerializer, IngredientSerializer,
    TagSerializer
)
from recipes.models import Ingredient, Tag
from users.models import Follow

User = get_user_model()


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        methods=('get',),
        detail=False
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(followed_by__follower=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            instance=pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsOwnerAdminOrReadOnly,)
    )
    def subscribe(self, request, id):
        follower = request.user
        followee = get_object_or_404(klass=User, id=id)

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                instance=followee,
                data=request.data,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(follower=follower, followee=followee)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        follow = get_object_or_404(
            klass=Follow, follower=follower, followee=followee
        )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ModelViewSet):
    """Вьюсет для тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsOwnerAdminOrReadOnly,)


class IngredientViewSet(ModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsOwnerAdminOrReadOnly,)
    # TO DO: filter search
