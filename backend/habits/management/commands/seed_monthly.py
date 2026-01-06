from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from habits.models import Habit, HabitEntry
from django.utils import timezone
import datetime as dt
import random


class Command(BaseCommand):
    help = "Seed sample habits and entries for current year/month testing"

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No user found. Create a user first.'))
            return

        # create example habits
        titles = ["Exercise", "Read", "Meditate"]
        habits = []
        for t in titles:
            h, _ = Habit.objects.get_or_create(user=user, title=t)
            habits.append(h)

        today = timezone.localdate()
        year = today.year

        # generate entries for each day of the year up to today
        start = dt.date(year, 1, 1)
        end = today
        day = start
        while day <= end:
            for h in habits:
                # random completion with weekly pattern bias
                completed = random.random() < (0.5 + (0.2 if day.weekday() < 5 else -0.1))
                HabitEntry.objects.update_or_create(habit=h, date=day, defaults={"completed": completed})
            day += dt.timedelta(days=1)

        self.stdout.write(self.style.SUCCESS('Seeded sample habits and entries for user: %s' % user.username))
