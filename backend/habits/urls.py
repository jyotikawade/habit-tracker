from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("add/", views.add_habit, name="add_habit"),
    path("toggle/<int:id>/", views.toggle_habit, name="toggle_habit"),
]
