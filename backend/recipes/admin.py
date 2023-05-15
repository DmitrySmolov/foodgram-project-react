from django.contrib.admin import ModelAdmin, site

from recipes.models import Tag


class TagAdmin(ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name', 'slug')
    ordering = ('name', )


site.register(Tag, TagAdmin)
