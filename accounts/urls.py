from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [

    path("", views.home, name="home"),
    path("login/", views.RoleBasedLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),

    path("register/", views.register_choice, name="register_choice"),
    path("register/patient/", views.patient_register, name="patient_register"),
    path("register/doctor/", views.doctor_register, name="doctor_register"),

    path("patient/", views.patient_dashboard, name="patient_dashboard"),
    path("doctor/", views.doctor_dashboard, name="doctor_dashboard"),
    path("admin/", views.admin_dashboard, name="admin_dashboard"),

    # 🔥 PROFILE
    path("profile/update/", views.profile_update, name="profile_update"),
    path("profile/delete/", views.profile_delete, name="profile_delete"),

    # 🔥 SCHEDULE
    path("doctor/schedule/create/", views.schedule_create, name="schedule_create"),

    # 🔥 CALENDAR
    path("doctor/calendar/events/", views.calendar_events, name="calendar_events"),
]