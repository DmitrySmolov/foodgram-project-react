from django.contrib.auth import get_user_model
from djoser.views import UserViewSet
from api.serializers import UserSerializer

User = get_user_model()


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
