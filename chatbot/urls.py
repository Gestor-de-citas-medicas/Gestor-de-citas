from django.urls import path
from . import views

urlpatterns = [
    path("message/", views.chat_message, name="chat_message"),
    path("history/", views.chat_history, name="chat_history"),
    path("clear/",   views.chat_clear,   name="chat_clear"),
]
