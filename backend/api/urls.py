from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import UserViewSet, TagViewSet, IngredientViewSet
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

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
