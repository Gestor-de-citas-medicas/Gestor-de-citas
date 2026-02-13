from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    home,
    RoleBasedLoginView,
    patient_dashboard,
    doctor_dashboard,
    admin_dashboard
)

urlpatterns = [
    path("", home, name="home"),  # ✅ ahora / existe y manda a /login/

    path("login/", RoleBasedLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("patient/", patient_dashboard, name="patient_dashboard"),
    path("doctor/", doctor_dashboard, name="doctor_dashboard"),
    path("admin-panel/", admin_dashboard, name="admin_dashboard"),
]
