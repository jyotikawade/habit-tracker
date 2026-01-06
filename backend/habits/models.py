
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class HabitEntry(models.Model):
    """Represents a single habit's completion state for a particular date.

    We keep per-day entries so we can aggregate month-wise and year-wise.
    """
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="entries")
    date = models.DateField()
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("habit", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.habit.title} @ {self.date} -> {self.completed}"
