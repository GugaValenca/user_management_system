from typing import cast

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserActivityLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name',
                    'last_name', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_email_verified', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)

    fieldsets = cast(tuple, UserAdmin.fieldsets) + (
        (
            'Custom Fields',
            {
                'fields': (
                    'role',
                    'profile_picture',
                    'phone_number',
                    'date_of_birth',
                    'bio',
                    'is_email_verified',
                    'last_login_ip',
                )
            },
        ),
    )


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__email', 'user__username', 'description')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)


admin.site.site_header = "User Management System Administration"
admin.site.site_title = "UMS Admin Portal"
admin.site.index_title = "Administration Dashboard"
