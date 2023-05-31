from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)
from rest_framework.viewsets import ModelViewSet
from users.models import Follow

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsActive, IsOwnerAdminOrReadOnly
from api.serializers import (IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeReadSerializer, SubscriptionSerializer,
                             TagSerializer, UserRecipeRelationSerializer,
                             UserSerializer)

User = get_user_model()


class AddRemoveMixin:
    """
    Миксин для типичных действий добавления/удаления подписки на другого
    пользователя, записи рецепта в избранное или в корзину пользователя.
    """
    def add_remove_action(self, request, id, model):
        user_field_name = self.add_remove_user_field_name
        instance_field_name = self.add_remove_instance_field_name
        user = request.user
        instance = get_object_or_404(
            self.get_queryset(),
            id=id
        )
        if request.method == 'POST':
            serializer = self.get_serializer(instance)
            serializer.validate()
            model.objects.create(
                **{
                    user_field_name: user, instance_field_name: instance
                }
            )

            return Response(
                data=serializer.data, status=HTTP_201_CREATED
            )
        if request.method == 'DELETE':
            relation = model.objects.filter(
                **{
                    user_field_name: user,
                    instance_field_name: instance
                }
            )
            if not relation.exists():
                model_name = model._meta.verbose_name
                raise ValidationError(
                    detail=f'Такой записи в {model_name} и не было.',
                    code=HTTP_400_BAD_REQUEST
                )
            relation.delete()
            return Response(status=HTTP_204_NO_CONTENT)


class UserViewSet(AddRemoveMixin, UserViewSet):
    """Вьюсет для работы с пользователями."""
    queryset = User.objects.all()
    add_remove_user_field_name = 'follower'
    add_remove_instance_field_name = 'followee'

    def is_owner(self, request, obj):
        return obj.followed_by.filter(follower=request.user).first()

    def get_permissions(self):
        if self.action == 'create':
            return (AllowAny(),)
        if (
            self.action == 'subscribe' and
            self.request.method == 'POST'
        ):
            return (IsActive(),)
        return (IsOwnerAdminOrReadOnly(),)

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
        return self.add_remove_action(request, id, Follow)


class TagViewSet(ModelViewSet):
    """Вьюсет для работы с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsOwnerAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(ModelViewSet):
    """Вьюсет для работы с  ингредиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsOwnerAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(AddRemoveMixin, ModelViewSet):
    """Вьюсет для работы с рецептами."""
    queryset = Recipe.objects.all()
    lookup_field = 'id'
    add_remove_user_field_name = 'user'
    add_remove_instance_field_name = 'recipe'
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        elif self.action in ('create', 'update'):
            return RecipeCreateUpdateSerializer
        elif self.action in ('shopping_cart', 'favorite'):
            return UserRecipeRelationSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()

        if (
            serializer_class == UserRecipeRelationSerializer and
            self.action in ('favorite', 'shopping_cart')
        ):
            kwargs['context'] = self.get_serializer_context()
            kwargs['model'] = (
                Favorite if self.action == 'favorite' else ShoppingCart
            )
        elif 'context' not in kwargs:
            kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_permissions(self):
        if self.action == 'create':
            return (IsActive(),)
        if (
            self.action in ('shopping_cart', 'favorite')
        ) and self.request.method == 'POST':
            return (IsActive(),)
        return (IsOwnerAdminOrReadOnly(),)

    def is_owner(self, request, obj):
        return obj.author == request.user

    @action(
        methods=('post', 'delete'),
        detail=True
    )
    def shopping_cart(self, request, id):
        return self.add_remove_action(request, id, ShoppingCart)

    @action(
        methods=('post', 'delete'),
        detail=True
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
            f"\u2022 {ingredient['ingredient__name']}"
            f" ({ingredient['ingredient__measurement_unit']})"
            f" -- {ingredient['amount']}"
            for ingredient in ingredients
        ])
        text += '\n\nFOODGRAM'
        filename = f'{user.get_username()}_shopping_cart.txt'
        response = HttpResponse(content=text, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
