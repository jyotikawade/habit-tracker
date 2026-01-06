from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("monthly/", views.monthly_page, name="monthly_page"),
    path("yearly/", views.yearly_page, name="yearly_page"),
    path("journal/", views.daily_journal_page, name="daily_journal"),
    path("add/", views.add_habit, name="add_habit"),
    path("toggle/<int:id>/", views.toggle_habit, name="toggle_habit"),
    path("api/monthly-progress/", views.monthly_progress, name="monthly_progress"),
    path("api/yearly-progress/", views.yearly_progress, name="yearly_progress"),
    path("api/habits-for-month/", views.habits_for_month, name="habits_for_month"),
    path("api/toggle-entry/", views.api_toggle_entry, name="api_toggle_entry"),
    path("api/journal/", views.api_journal, name="api_journal"),
    
]
