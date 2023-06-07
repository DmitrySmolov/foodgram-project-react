from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

app_name = 'api'

router = DefaultRouter()

router.register(
    prefix='users', viewset=UserViewSet, basename='users'
)
router.register(
    prefix='tags', viewset=TagViewSet, basename='tags'
)
router.register(
    prefix='ingredients', viewset=IngredientViewSet, basename='ingredients'
)
router.register(
    prefix='recipes', viewset=RecipeViewSet, basename='recipes'
)

custom_user_patterns = [
    path(
        route='users/subscriptions/',
        view=UserViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions'
    ),
    path(
        route='users/<int:id>/subscribe/',
        view=UserViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}),
        name='user-subscribe'
    ),
]

urlpatterns = [
    path('', include(custom_user_patterns)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
