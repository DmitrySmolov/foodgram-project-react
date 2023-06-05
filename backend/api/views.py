from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import (IsActive, IsAdminOrReadOnly,
                             IsAuthorAdminOrReadOnly,
                             IsFollowerAdminOrReadOnly)
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeReadSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer, TagSerializer,
                             UserSerializer)
from foodgram.settings import SHOPPING_CART_CONTENT_TYPE
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag

User = get_user_model()


class AddRemoveMixin:
    """
    Миксин для типичных действий добавления/удаления подписки на другого
    пользователя, записи рецепта в избранное или в корзину пользователя.
    """
    def add_remove_action(self, request, context):
        data = request.data if request.method == 'POST' else {}
        serializer = self.get_serializer(
            data=data, context=context
        )
        if not serializer.is_valid(raise_exception=True):
            return Response(
                serializer.errors,
                status=HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            serializer.save()
            return Response(
                data=serializer.data, status=HTTP_201_CREATED
            )
        if request.method == 'DELETE':
            serializer.delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(status=HTTP_400_BAD_REQUEST)


class UserViewSet(AddRemoveMixin, UserViewSet):
    """Вьюсет для работы с пользователями."""
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == 'create':
            return (AllowAny(),)
        if (
            self.action == 'subscribe' and
            self.request.method == 'POST'
        ):
            return (IsActive(),)
        return (IsFollowerAdminOrReadOnly(),)

    def get_serializer_class(self):
        if self.action == 'subscribe':
            return SubscriptionSerializer
        return UserSerializer

    @action(
        methods=('get',),
        detail=False
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(followed_by__follower=request.user)
        recipes_limit = request.query_params.get('recipes_limit')
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            instance=pages,
            many=True,
            context={
                'request': request,
                'recipes_limit': recipes_limit
            }
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=('post', 'delete'),
        detail=True
    )
    def subscribe(self, request, id):
        context = {'request': request, 'followee_id': id}
        if request.method == 'POST':
            request.data['followee'] = id
        return self.add_remove_action(request, context)


class TagViewSet(ModelViewSet):
    """Вьюсет для работы с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(ModelViewSet):
    """Вьюсет для работы с  ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(AddRemoveMixin, ModelViewSet):
    """Вьюсет для работы с рецептами."""
    queryset = Recipe.objects.all()
    lookup_field = 'id'
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        if self.action in ('create', 'update'):
            return RecipeCreateUpdateSerializer
        if self.action == 'favorite':
            return FavoriteSerializer
        if self.action == 'shopping_cart':
            return ShoppingCartSerializer
        return RecipeReadSerializer

    def get_permissions(self):
        if self.action == 'create':
            return (IsActive(),)
        if (
            self.action in ('shopping_cart', 'favorite')
        ) and self.request.method == 'POST':
            return (IsActive(),)
        return (IsAuthorAdminOrReadOnly(),)

    @action(
        methods=('post', 'delete'),
        detail=True
    )
    def shopping_cart(self, request, id):
        context = {'request': request, 'recipe_id': id}
        if request.method == 'POST':
            request.data['recipe'] = id
        return self.add_remove_action(request, context)

    @action(
        methods=('post', 'delete'),
        detail=True
    )
    def favorite(self, request, id):
        context = {'request': request, 'recipe_id': id}
        if request.method == 'POST':
            request.data['recipe'] = id
        return self.add_remove_action(request, context)

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
            f"\u2022 {ingredient['ingredient__name']}"
            f" ({ingredient['ingredient__measurement_unit']})"
            f" -- {ingredient['amount']}"
            for ingredient in ingredients
        ])
        text += '\n\nFOODGRAM'
        filename = f'{user.get_username()}_shopping_cart.txt'
        response = HttpResponse(
            content=text, content_type=SHOPPING_CART_CONTENT_TYPE
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
