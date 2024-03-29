from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import (BooleanFilter, CharFilter,
                                                   ModelMultipleChoiceFilter)

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')
    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug'
    )

    class Meta:
        model = Recipe
        fields = ('author',)

    def filter_is_favorited(self, queryset, _, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset
        if not value:
            return queryset.exclude(favorited_by__user=user)
        return queryset.filter(favorited_by__user=user)

    def filter_is_in_shopping_cart(self, queryset, _, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset
        if not value:
            return queryset.exclude(shopped_by__user=user)
        return queryset.filter(shopped_by__user=user)


class IngredientFilter(FilterSet):
    name = CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def filter_name(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value))
