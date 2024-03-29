from django.contrib.admin import ModelAdmin, TabularInline, display, register

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class IngredientInRecipeInline(TabularInline):
    model = IngredientInRecipe
    extra = 1


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    inlines = (IngredientInRecipeInline,)
    list_display = ('name', 'author', 'added_to_favorite')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags__name',)

    @display(description='В избранных (кол-во раз)')
    def added_to_favorite(self, obj):
        return obj.favorited_by.count()


@register(IngredientInRecipe)
class IngredientInRecipeAdmin(ModelAdmin):
    list_display = ('recipe', 'amount', 'ingredient')
    search_fields = (
        'recipe__author__username', 'recipe__author__email',
        'recipe__name', 'ingredient__name'
    )
    list_filter = ('recipe__tags__name',)


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_filter = ('recipe__tags__name',)


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
    list_filter = ('recipe__tags__name',)
