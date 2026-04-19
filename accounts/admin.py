from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import OrganizerProfile, StudentOTP, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    list_display = ("username", "email", "role", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "signature_image")


@admin.register(StudentOTP)
class StudentOTPAdmin(admin.ModelAdmin):
    list_display = ("email", "code", "created_at", "used_at")
    list_filter = ("used_at",)
    search_fields = ("email",)
