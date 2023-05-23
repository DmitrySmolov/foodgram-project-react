from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.serializers import ModelSerializer, SerializerMethodField

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
