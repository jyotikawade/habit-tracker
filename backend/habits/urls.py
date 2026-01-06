from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("add/", views.add_habit, name="add_habit"),
    path("toggle/<int:id>/", views.toggle_habit, name="toggle_habit"),
    path("api/monthly-progress/", views.monthly_progress, name="monthly_progress"),
    path("api/yearly-progress/", views.yearly_progress, name="yearly_progress"),
]
