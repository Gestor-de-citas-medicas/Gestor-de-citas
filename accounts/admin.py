from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DoctorSchedule

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ("doctor", "day_number", "start_time", "end_time")
    list_filter = ("doctor", "day_number")
