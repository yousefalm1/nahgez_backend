from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_phone_number', 'get_gender')
    list_select_related = ('profile', )
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__phone_number')
    ordering = ('-date_joined',)

    def get_phone_number(self, instance):
        return instance.profile.phone_number if hasattr(instance, 'profile') else ''
    get_phone_number.short_description = 'Phone Number'

    def get_gender(self, instance):
        return instance.profile.get_gender_display() if hasattr(instance, 'profile') else ''
    get_gender.short_description = 'Gender'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'gender', 'created_at', 'updated_at')
    list_filter = ('gender', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number', 'gender')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
