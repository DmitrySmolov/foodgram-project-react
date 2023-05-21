from django.contrib.admin import ModelAdmin, register

from users.models import Follow, User


@register(User)
class UserAdmin(ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_active'
    )
    list_editable = ('is_active',)
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')


@register(Follow)
class FollowAdmin(ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')
    list_filter = ('user__username', 'author__username')
