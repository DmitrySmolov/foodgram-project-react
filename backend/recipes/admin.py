from django.contrib.admin import ModelAdmin, register, display

from recipes.models import (
    Tag, Ingredient, Recipe, IngredientInRecipe,
    Favorite
)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name', 'measurement_unit')


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'author', 'added_to_favorite')
    search_fields = ('name', 'author__username')
    list_filter = ('name', 'author__username', 'tags__name')

    @display(description='В избранных (кол-во раз)')
    def added_to_favorite(self, obj):
        return obj.favorited.count()


@register(IngredientInRecipe)
class IngredientInRecipeAdmin(ModelAdmin):
    list_display = ('recipe', 'amount', 'ingredient')
    search_fields = ('recipe__name', 'ingredient__name')
    list_filter = ('recipe__name', 'ingredient__name')


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user__username', 'recipe__name')
