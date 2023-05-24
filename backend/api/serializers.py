from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, SerializerMethodField
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
            user.follows.filter(author=obj).exists()
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
        if (
            request.path == reverse('api:users-list') and
            request.method == "POST"
        ):
            representation.pop('is_subscribed')
        representation.pop('password')
        return representation


class SubscriptionSerializer(UserSerializer):
    recipes = ShortRecipeSerializer(many=True)
    recipes_count = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )
        read_only_fields = '__all__'

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def validate(self, data):
        user = self.context.get('request').user
        author = self.instance
        if Follow.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                detail=(
                    'Вы уже подписаны на пользователя '
                    f'{author.get_username()}.'
                ),
                code=status.HTTP_400_BAD_REQUEST
            )
        if user.pk == author.pk:
            raise ValidationError(
                detail='Нельзя подписываться на самого себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return {}
