from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import UserViewSet
app_name = 'api'

router = DefaultRouter()

router.register(
    prefix='users', viewset=UserViewSet, basename='users'
)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
