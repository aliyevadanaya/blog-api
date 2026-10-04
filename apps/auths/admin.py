from django.contrib import admin

from .models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    """CustomUser model admin configuration class"""
    list_display = ('email', 'first_name', 'last_name')
    

admin.site.register(CustomUser, CustomUserAdmin)

