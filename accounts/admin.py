from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# Línea 3 — actualizar el import
from .models import User, DoctorSchedule, ScheduleException, DoctorProfile

# Al final del archivo — agregar esto
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display  = ("full_name", "specialty", "license_number", "phone")
    list_filter   = ("specialty",)
    search_fields = ("full_name", "license_number")

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    list_display  = ("username", "email", "role", "is_staff", "is_active")
    list_filter   = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display  = ("doctor", "get_day", "start_time", "end_time", "is_active")
    list_filter   = ("day_number", "is_active")
    search_fields = ("doctor__username",)
    list_editable = ("is_active",)          # activar/pausar directo desde la lista
    ordering      = ("doctor", "day_number", "start_time")

    @admin.display(description="Día")
    def get_day(self, obj):
        return obj.get_day_number_display()


@admin.register(ScheduleException)
class ScheduleExceptionAdmin(admin.ModelAdmin):
    list_display  = ("doctor", "date", "start_time", "end_time", "type", "reason")
    list_filter   = ("type", "date")
    search_fields = ("doctor__username", "reason")
    ordering      = ("-date", "start_time")
    date_hierarchy = "date"                 # navegador por fecha en la parte superior