from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.status import (
    HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
)
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from api.permissions import IsOwnerAdminOrReadOnly, IsActive
from api.serializers import (
    UserSerializer, SubscriptionSerializer, IngredientSerializer,
    TagSerializer, RecipeCreateUpdateSerializer, RecipeReadSerializer
)
from recipes.models import (
    Ingredient, IngredientInRecipe, Tag, Recipe, Favorite, ShoppingCart
)
from users.models import Follow

User = get_user_model()


class AddRemoveMixin:
    """
    Миксин для типичных действий добавления/удаления подписки на другого
    пользователя, записи рецепта в избранное или в корзину.
    """
    def add_remove_action(self, request, id, action_model):
        user = request.user
        instance = self.get_object()
        if request.method == 'POST':
            action_model.objects.create(**{
                self.add_remove_user_field_name: user,
                self.add_remove_instance_field_name: instance
            })
            return Response(status=HTTP_201_CREATED)
        if request.method == 'DELETE':
            action = get_object_or_404(action_model, **{
                self.add_remove_user_field_name: user,
                self.add_remove_instance_field_name: instance
            })
            action.delete()
            return Response(status=HTTP_204_NO_CONTENT)


class UserViewSet(AddRemoveMixin, UserViewSet):
    """Вьюсет для работы с пользователями."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    add_remove_user_field_name = 'follower'
    add_remove_instance_field_name = 'followee'

    def is_owner(self, request, obj):
        return obj.followed_by.filter(follower=request.user).first()

    def get_permissions(self):
        if self.action == 'create':
            return (AllowAny(),)
        return super().get_permissions()

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
        return self.add_remove_action(request, id, Follow)


class TagViewSet(ModelViewSet):
    """Вьюсет для работы с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsOwnerAdminOrReadOnly,)


class IngredientViewSet(ModelViewSet):
    """Вьюсет дляработы с  ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsOwnerAdminOrReadOnly,)
    # TO DO: filter search


class RecipeViewSet(AddRemoveMixin, ModelViewSet):
    """Вьюсет для работы с рецептами."""
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerAdminOrReadOnly,)
    add_remove_user_field_name = 'user'
    add_remove_instance_field_name = 'recipe'
    # TO DO: filter search

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        elif self.action in ('create', 'update'):
            return RecipeCreateUpdateSerializer

    def is_owner(self, request, obj):
        return obj.author == request.user

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsOwnerAdminOrReadOnly,)
    )
    def shopping_cart(self, request, id):
        return self.add_remove_action(request, id, ShoppingCart)

    @action(
        methods=('post', 'delete'),
        detail=True,
        permission_classes=(IsOwnerAdminOrReadOnly,)
    )
    def favorite(self, request, id):
        return self.add_remove_action(request, id, Favorite)

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsActive,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shops_for.exists():
            return Response(
                data={"detail": "Ваш список покупок пуст."},
                status=HTTP_400_BAD_REQUEST
                )
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopped_by__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        text = 'ВАШ СПИСОК ПОКУПОК: \n\n'
        text += '\n'.join([
            f"- {ingredient['ingredient__name']}"
            f" ({ingredient['ingredient__measurement_unit']})"
            f" -- {ingredient['amount']}"
            for ingredient in ingredients
        ])
        text += '\n\nFOODGRAM'
        filename = f'{user.get_username()}_shopping_cart.txt'
        response = HttpResponse(content=text, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
