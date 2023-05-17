from django.contrib.admin import ModelAdmin, register

from recipes.models import Tag, Ingredient


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')
    ordering = ('name', )


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name', 'measurement_unit')
    ordering = ('name', )
