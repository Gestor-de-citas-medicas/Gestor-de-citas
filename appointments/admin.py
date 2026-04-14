from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ("id", "patient", "doctor", "date", "start_time", "end_time", "status")
    list_filter   = ("status", "date", "doctor")
    search_fields = ("patient__username", "doctor__username", "reason")
    ordering      = ("-date", "start_time")
