import base64
import re
import uuid
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    ModelSerializer, SerializerMethodField, PrimaryKeyRelatedField,
    ReadOnlyField, ImageField, CurrentUserDefault, HiddenField
)
from recipes.models import (
    Tag, Ingredient, Recipe, IngredientInRecipe
)
from users.models import Follow

User = get_user_model()


class UserSerializer(ModelSerializer):
    """Сериализатор модели пользователя."""
    is_subscribed = SerializerMethodField()

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
            user is not obj and
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
            request.method == "POST"
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


class SubscriptionSerializer(UserSerializer):
    """Сериализатор сервиса подписок."""
    recipes = SimpleRecipeSerializer(many=True)
    recipes_count = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count'
        )
        read_only_fields = fields

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def validate(self):
        follower = self.context.get('request').user
        followee = self.instance
        if Follow.objects.filter(
            follower=follower, followee=followee
        ).exists():
            raise ValidationError(
                detail=(
                    'Вы уже подписаны на пользователя '
                    f'{followee.get_username()}.'
                ),
                code=status.HTTP_400_BAD_REQUEST
            )
        if follower.pk == followee.pk:
            raise ValidationError(
                detail='Нельзя подписываться на самого себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return {}


class TagSerializer(ModelSerializer):
    """Сериализатор тегов."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(ModelSerializer):
    """Общий сериализатор ингредиентов."""
    class Meta:
        model = Ingredient
        fields = '__all__'


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
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and (
            re.match(r'^/api/users/[^/]+/subscribe$', request.path) or
            request.path == '/api/users/subscriptions'
        ):
            trimmed_fields = ('id', 'name', 'image', 'cooking_time')
            return {field: representation[field] for field in trimmed_fields}

        return representation


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
            if item['amount'] < 1:
                raise ValidationError(
                    detail='В рецепте есть ингредиент в количестве меньше 1.'
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
        if value < 1:
            raise ValidationError(
                detail='Указано время приготовления меньше 1 минуты.'
            )
        return value

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


class UserRecipeRelationSerializer(SimpleRecipeSerializer):
    """
    Сериализатор для работы с типичными связями 'пользователь-рецепт':
    список избранного или список покупок.
    """
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', None)
        super().__init__(*args, **kwargs)

    def validate(self):
        user = self.context.get('request').user
        recipe = self.instance
        if self.model.objects.filter(
            user=user, recipe=recipe
        ).exists():
            model_name = self.model._meta.verbose_name
            raise ValidationError(
                detail=(
                    f'Вы уже добавляли этот рецепт в {model_name}.'
                ),
                code=status.HTTP_400_BAD_REQUEST
            )
        return {}
