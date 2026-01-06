from django.contrib import admin
from .models import Habit, HabitEntry


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
	list_display = ("title", "user")


@admin.register(HabitEntry)
class HabitEntryAdmin(admin.ModelAdmin):
	list_display = ("habit", "date", "completed")
	list_filter = ("date", "completed")
