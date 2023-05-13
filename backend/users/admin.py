from django.contrib import admin

from users.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_active'
    )
    list_editable = ('is_active',)
    search_fields = ('username', 'email')
    list_filter = ('username', 'email')
    ordering = ('username', )


admin.site.register(User, UserAdmin)
