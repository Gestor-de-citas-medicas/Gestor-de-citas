from django.urls import path
from . import views

urlpatterns = [

    path("buscar-doctor/", views.buscar_doctor, name="buscar_doctor"),

    path('disponibilidad-ajax/<int:doctor_id>/', views.disponibilidad_ajax, name='disponibilidad_ajax'),
    path('disponibilidad/<int:doctor_id>/', views.disponibilidad, name='disponibilidad'),


]