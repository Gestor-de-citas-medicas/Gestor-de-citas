from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    home,
    RoleBasedLoginView,
    register_choice,
    patient_register,
    doctor_register,
    patient_dashboard,
    doctor_dashboard,
    admin_dashboard,
    schedule_create,
    schedule_toggle,
    schedule_delete,
    exception_create,
    exception_update,
    exception_delete,
    calendar_events,
)

urlpatterns = [
    path("", home, name="home"),
    path("login/", RoleBasedLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("register/", register_choice, name="register_choice"),
    path("register/patient/", patient_register, name="patient_register"),
    path("register/doctor/", doctor_register, name="doctor_register"),

    path("patient/", patient_dashboard, name="patient_dashboard"),
    path("doctor/", doctor_dashboard, name="doctor_dashboard"),
    path("admin-panel/", admin_dashboard, name="admin_dashboard"),

    path("doctor/schedule/create/", schedule_create, name="schedule_create"),
    path("doctor/schedule/<int:pk>/toggle/", schedule_toggle, name="schedule_toggle"),
    path("doctor/schedule/<int:pk>/delete/", schedule_delete, name="schedule_delete"),

    path("doctor/exception/create/", exception_create, name="exception_create"),
    path("doctor/exception/<int:pk>/update/", exception_update, name="exception_update"),
    path("doctor/exception/<int:pk>/delete/", exception_delete, name="exception_delete"),

    path("doctor/calendar/events/", calendar_events, name="calendar_events"),
]