from django.contrib.admin import ModelAdmin, site

from users.models import Follow, User


class UserAdmin(ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_active'
    )
    list_editable = ('is_active',)
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')
    ordering = ('username', )


class FollowAdmin(ModelAdmin):
    list_display = (
        'user',
        'author',
    )
    search_fields = ('user', 'author', )
    list_filter = ('user', 'author', )


site.register(User, UserAdmin)
site.register(Follow, FollowAdmin)
