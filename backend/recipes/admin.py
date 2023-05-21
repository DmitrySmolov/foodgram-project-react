from django.contrib.admin import ModelAdmin, register

from recipes.models import Tag, Ingredient, Recipe, IngredientInRecipe


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
    list_display = ('name', 'author')
    search_fields = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    # Доделать: На странице рецепта вывести общее
    # число добавлений этого рецепта в избранное.


@register(IngredientInRecipe)
class IngredientInRecipeAdmin(ModelAdmin):
    list_display = ('recipe', 'amount', 'ingredient')
    search_fields = ('recipe', 'ingredient')
    list_filter = ('recipe', 'ingredient')
