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
    list_display = ('follower', 'followee')
    search_fields = (
        'follower__username', 'follower__email',
        'followee__username', 'followee__email',
    )
