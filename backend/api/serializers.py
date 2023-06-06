import base64
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (CurrentUserDefault, HiddenField,
                                        ImageField, ModelSerializer,
                                        PrimaryKeyRelatedField, ReadOnlyField,
                                        SerializerMethodField)
from rest_framework.validators import UniqueTogetherValidator

from foodgram.settings import MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class UserSerializer(ModelSerializer):
    """Сериализатор модели пользователя."""
    is_subscribed = SerializerMethodField(method_name='get_is_subscribed')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated and
            user.follows.filter(followee=obj).exists()
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        instance = self.Meta.model(**validated_data)
        instance.set_password(password)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and (
            request.path == reverse('api:users-list') and
            request.method == 'POST'
        ):
            representation.pop('is_subscribed')
        representation.pop('password')
        return representation


class SimpleRecipeSerializer(ModelSerializer):
    """
    Сериализатор для упрощённого отображения рецептов при работе с подписками
    и списками избранного и покупок."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionSerializer(ModelSerializer):
    """Сериализатор сервиса подписок."""
    follower = HiddenField(default=CurrentUserDefault())
    followee = PrimaryKeyRelatedField(queryset=User.objects.all())
    recipes = SerializerMethodField(method_name='get_recipes')
    recipes_count = SerializerMethodField(method_name='get_recipes_count')

    class Meta:
        model = Follow
        fields = ('follower', 'followee', 'recipes', 'recipes_count')
        read_only_fields = ('recipes', 'recipes_count')
        validators = (
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('follower', 'followee'),
                message=(
                    'Вы уже подписаны на этого пользователя.'
                )
            ),
        )

    def get_recipes(self, obj):
        limit = self.context.get('recipes_limit')
        recipes = obj.followee.recipes.all()
        if limit:
            recipes = recipes[int(limit):]
        return SimpleRecipeSerializer(instance=recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.followee.recipes.count()

    def is_valid(self, raise_exception=False):
        if self.context['request'].method == 'DELETE':
            return True
        return super().is_valid(raise_exception=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        follower = request.user
        followee = attrs.get('followee')
        if request.method == 'POST' and follower.pk == followee.pk:
            raise ValidationError(
                detail='Нельзя подписываться на самого себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return attrs

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        serializer = self.__class__(instance, context=self.context)
        return serializer.data

    def delete(self):
        request = self.context.get('request')
        follower = request.user
        followee_id = self.context.get('followee_id')
        followee = get_object_or_404(User, id=followee_id)
        follow = Follow.objects.filter(
            follower=follower, followee=followee
        )
        if not follow.exists():
            raise ValidationError(
                detail=(
                    'Вы и так не подписаны на пользователя'
                    f' {followee.get_username()}.'
                ),
                code=status.HTTP_400_BAD_REQUEST
            )
        follow.delete()

    def to_representation(self, instance):
        followee_serializer = UserSerializer(
            instance.followee, context=self.context
        )
        representation = followee_serializer.data
        representation['recipes'] = self.get_recipes(instance)
        representation['recipes_count'] = self.get_recipes_count(instance)
        return representation


class SubscriptionsListSerializer(ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""
    recipes = SerializerMethodField(method_name='get_recipes')
    recipes_count = SerializerMethodField(method_name='get_recipes_count')
    is_subscribed = SerializerMethodField(method_name='get_is_subscribed')

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )
        read_only_fields = fields

    def get_recipes(self, obj):
        limit = self.context.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return SimpleRecipeSerializer(instance=recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated and
            user.follows.filter(followee=obj).exists()
        )


class TagSerializer(ModelSerializer):
    """Сериализатор тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):
    """Общий сериализатор ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(ModelSerializer):
    """Сериализатор для работы с ингрединтами в рецепте."""
    id = PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeReadSerializer(ModelSerializer):
    """Сериализатор для чтения рецептов."""
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True
    )
    is_favorited = SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated and
            user.favorites.filter(recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated and
            user.shops_for.filter(recipe=obj).exists()
        )


class Base64ImageField(ImageField):
    """
    Кастомный тип поля для работы с картинками в формате строки base64.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            id = uuid.uuid4()
            data = ContentFile(
                base64.b64decode(imgstr), name=id.urn[9:] + "." + ext
            )
        return super().to_internal_value(data)


class RecipeCreateUpdateSerializer(ModelSerializer):
    """Сериализатор для создания и изменения рецепта."""
    author = HiddenField(default=CurrentUserDefault())
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField(
        max_length=None, use_url=True
    )

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError(
                detail='В рецепте нет ингредиентов.'
            )
        ingredients = []
        for item in value:
            ingredient = item.get('ingredient')
            if not ingredient:
                raise ValidationError(
                    detail='В рецепте указаны недоступные ингредиенты.'
                )
            if item in ingredients:
                raise ValidationError(
                    detail='В рецепте повторяются ингредиенты.'
                )
            if item['amount'] < MIN_INGREDIENT_AMOUNT:
                raise ValidationError(
                    detail=(
                        'В рецепте есть ингредиент в количестве '
                        f'меньше {MIN_INGREDIENT_AMOUNT}.'
                    )
                )
            ingredients.append(item)
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError(
                detail='В рецепте нет ни одного тега.'
            )
        tags = []
        for item in value:
            if not Tag.objects.filter(id=item.id).exists():
                raise ValidationError(
                    detail='В рецепте указаны недоступные теги.'
                )
            if item in tags:
                raise ValidationError(
                    detail='В рецепте повторяются теги.'
                )
            tags.append(item)
        return value

    def validate_cooking_time(self, value):
        if value < MIN_COOKING_TIME:
            raise ValidationError(
                detail=(
                    f'Указано время приготовления меньше {MIN_COOKING_TIME}'
                    ' минуты.'
                )
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        for tag_data in tags_data:
            recipe.tags.add(tag_data)
        for ingredient_data in ingredients_data:
            IngredientInRecipe.objects.create(recipe=recipe, **ingredient_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.save()
        instance.tags.clear()
        for tag_data in tags_data:
            instance.tags.add(tag_data)
        instance.ingredients.clear()
        for ingredient_data in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=instance, **ingredient_data
            )
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(ModelSerializer):
    """Сериализатор работы с избранным."""
    user = HiddenField(default=CurrentUserDefault())
    recipe = PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe')
            ),
        )

    def is_valid(self, raise_exception=False):
        if self.context['request'].method == 'DELETE':
            return True
        return super().is_valid(raise_exception=True)

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        serializer = self.__class__(instance, context=self.context)
        return serializer.data

    def delete(self):
        request = self.context.get('request')
        user = request.user
        recipe_id = self.context.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        favorite = Favorite.objects.filter(
            user=user, recipe=recipe
        )
        if not favorite.exists():
            raise ValidationError(
                detail=(
                    f'У вас и так {recipe.name} не в избранном.'
                ),
                code=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()

    def to_representation(self, instance):
        recipe_serializer = SimpleRecipeSerializer(
            instance.recipe, context=self.context
        )
        return recipe_serializer.data


class ShoppingCartSerializer(ModelSerializer):
    """Сериализатор работы с корзиной."""
    user = HiddenField(default=CurrentUserDefault())
    recipe = PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = (
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe')
            ),
        )

    def is_valid(self, raise_exception=False):
        if self.context['request'].method == 'DELETE':
            return True
        return super().is_valid(raise_exception=True)

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        serializer = self.__class__(instance, context=self.context)
        return serializer.data

    def delete(self):
        request = self.context.get('request')
        user = request.user
        recipe_id = self.context.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        favorite = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        )
        if not favorite.exists():
            raise ValidationError(
                detail=(
                    f'У вас и так {recipe.name} не в корзине.'
                ),
                code=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()

    def to_representation(self, instance):
        recipe_serializer = SimpleRecipeSerializer(
            instance.recipe, context=self.context
        )
        return recipe_serializer.data
