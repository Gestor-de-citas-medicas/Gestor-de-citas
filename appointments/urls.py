from django.urls import path
from . import views

urlpatterns = [
    path("",        views.appointment_list,   name="appointment_list"),
    path("new/",    views.appointment_create, name="appointment_create"),
    path("<int:pk>/cancel/", views.appointment_cancel, name="appointment_cancel"),
    path("<int:pk>/confirm/", views.appointment_confirm, name="appointment_confirm"),
    path("<int:pk>/complete/", views.appointment_complete, name="appointment_complete"),
    path("<int:pk>/review/", views.review_create, name="review_create"),
    path("doctor/<int:pk>/reviews/", views.doctor_reviews, name="doctor_reviews"),
    path("api/available-slots/", views.available_slots_api, name="available_slots_api"),
]
