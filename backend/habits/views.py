from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Habit, HabitEntry
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import calendar
import datetime as dt


def _today_date():
    return timezone.localdate()


@login_required
def home(request):
    habits = Habit.objects.filter(user=request.user)
    today = _today_date()
    entries = HabitEntry.objects.filter(habit__in=habits, date=today)
    today_map = {e.habit_id: e.completed for e in entries}
    # attach today's state to habit instances for template convenience
    for h in habits:
        h.today_completed = today_map.get(h.id, False)
    return render(request, "home.html", {"habits": habits, "today_map": today_map})


@login_required
def add_habit(request):
    if request.method == "POST":
        title = request.POST['title']
        Habit.objects.create(user=request.user, title=title)
        return redirect("home")
    return render(request, "add_habit.html")


@login_required
def toggle_habit(request, id):
    habit = get_object_or_404(Habit, id=id, user=request.user)
    today = _today_date()
    entry, created = HabitEntry.objects.get_or_create(habit=habit, date=today, defaults={"completed": True})
    if not created:
        entry.completed = not entry.completed
        entry.save()
    return redirect("home")


@login_required
def monthly_progress(request):
    user = request.user
    today = _today_date()
    year = today.year
    month = today.month
    _, ndays = calendar.monthrange(year, month)
    total_habits = Habit.objects.filter(user=user).count() or 0
    days = []
    counts = []
    percentages = []
    labels = []
    for day in range(1, ndays + 1):
        d = dt.date(year, month, day)
        cnt = HabitEntry.objects.filter(habit__user=user, date=d, completed=True).count()
        pct = round((cnt / total_habits * 100) if total_habits else 0, 1)
        days.append(day)
        counts.append(cnt)
        percentages.append(pct)
        labels.append(d.isoformat())
    return JsonResponse({"days": days, "counts": counts, "percentages": percentages, "labels": labels})


@login_required
def yearly_progress(request):
    user = request.user
    today = _today_date()
    year = today.year
    monthly_counts = []
    monthly_pct = []
    labels = []
    total_habits = Habit.objects.filter(user=user).count() or 0
    for month in range(1, 13):
        _, ndays = calendar.monthrange(year, month)
        start = dt.date(year, month, 1)
        end = dt.date(year, month, ndays)
        cnt = HabitEntry.objects.filter(habit__user=user, date__gte=start, date__lte=end, completed=True).count()
        pct = round((cnt / (total_habits * ndays) * 100) if total_habits else 0, 1)
        monthly_counts.append(cnt)
        monthly_pct.append(pct)
        labels.append(f"{year}-{month:02d}")
    return JsonResponse({"months": labels, "counts": monthly_counts, "percentages": monthly_pct})
