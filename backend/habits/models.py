
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    def __str__(self):
        return self.title
    class Meta:
        indexes = [models.Index(fields=["user"])]


class HabitEntry(models.Model):
    """Represents a single habit's completion state for a particular date.

    We keep per-day entries so we can aggregate month-wise and year-wise.
    """
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="entries")
    # Denormalized user to avoid JOINs when querying by user (speeds up large-scale aggregations)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True, editable=False)
    date = models.DateField()
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("habit", "date")
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["habit", "date"]),
            models.Index(fields=["user", "date", "completed"]),
        ]

    def __str__(self):
        return f"{self.habit.title} @ {self.date} -> {self.completed}"

    def save(self, *args, **kwargs):
        # ensure `user` is populated to keep denormalized column consistent
        if not getattr(self, 'user_id', None) and getattr(self, 'habit', None):
            try:
                self.user = self.habit.user
            except Exception:
                pass
        super().save(*args, **kwargs)


class JournalEntry(models.Model):
    """Simple daily journal entry per user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    text = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "date")
        indexes = [models.Index(fields=["user", "date"])]

    def __str__(self):
        return f"Journal {self.user.username} @ {self.date}"
