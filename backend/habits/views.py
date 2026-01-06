from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Habit, HabitEntry, JournalEntry
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
def monthly_page(request):
    # page focused on selected month
    return render(request, "monthly.html", {})


@login_required
def yearly_page(request):
    return render(request, "yearly.html", {})


@login_required
def habits_page(request):
    return render(request, "habits.html", {})


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
    try:
        entry, created = HabitEntry.objects.get_or_create(habit=habit, date=today, defaults={"completed": True, "user": request.user})
    except Exception:
        # fallback: create and ensure save() sets user
        entry, created = HabitEntry.objects.get_or_create(habit=habit, date=today, defaults={"completed": True})
    if not created:
        entry.completed = not entry.completed
        entry.save()
    return redirect("home")


@login_required
def monthly_progress(request):
    user = request.user
    today = _today_date()
    # allow client to pass year/month, default to current
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
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
        # use denormalized `user` column for faster lookup (avoids JOIN to Habit)
        cnt = HabitEntry.objects.filter(user=user, date=d, completed=True).count()
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
    try:
        year = int(request.GET.get('year', today.year))
    except (TypeError, ValueError):
        year = today.year
    monthly_counts = []
    monthly_pct = []
    labels = []
    total_habits = Habit.objects.filter(user=user).count() or 0
    for month in range(1, 13):
        _, ndays = calendar.monthrange(year, month)
        start = dt.date(year, month, 1)
        end = dt.date(year, month, ndays)
        cnt = HabitEntry.objects.filter(user=user, date__gte=start, date__lte=end, completed=True).count()
        pct = round((cnt / (total_habits * ndays) * 100) if total_habits else 0, 1)
        monthly_counts.append(cnt)
        monthly_pct.append(pct)
        labels.append(f"{year}-{month:02d}")
    return JsonResponse({"months": labels, "counts": monthly_counts, "percentages": monthly_pct})


@login_required
def habits_for_month(request):
    """Return all habits for the user with per-day completion flags for a selected month."""
    user = request.user
    today = _today_date()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
        year = today.year
        month = today.month

    _, ndays = calendar.monthrange(year, month)
    out = []

    habits = Habit.objects.filter(user=user)
    for h in habits:
        # 1️⃣ Query existing entries for month
        entries = HabitEntry.objects.filter(habit=h, date__year=year, date__month=month)
        entry_map = {e.date.day: e.completed for e in entries}

        # Only create if really missing, but don't overwrite anything
        if year == today.year and month == today.month and today.day not in entry_map:
            e = HabitEntry.objects.create(habit=h, date=today, completed=False, user=user)
            entry_map[today.day] = e.completed

        # 3️⃣ Build per-day list
        days = []
        completed_count = 0
        for d in range(1, ndays + 1):
            completed = entry_map.get(d, False)
            days.append({"day": d, "completed": completed})
            if completed:
                completed_count += 1

        pct = round((completed_count / ndays * 100), 1) if ndays else 0
        out.append({
            "id": h.id,
            "title": h.title,
            "days": days,
            "completed_count": completed_count,
            "percentage": pct
        })

    return JsonResponse({"habits": out, "ndays": ndays})


@login_required
def daily_journal_page(request):
    return render(request, "daily_journal.html", {})


@login_required
def api_journal(request):
    user = request.user
    if request.method == 'GET':
        date_str = request.GET.get('date')
        if date_str:
            try:
                d = dt.date.fromisoformat(date_str)
            except Exception:
                return JsonResponse({"error": "invalid date"}, status=400)
        else:
            d = _today_date()
        entries = JournalEntry.objects.filter(user=user, date=d)
        if entries.exists():
            return JsonResponse({"date": d.isoformat(), "text": entries.first().text})
        return JsonResponse({"date": d.isoformat(), "text": ""})

    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body.decode())
        except Exception:
            data = request.POST or {}
        date_str = data.get('date')
        text = data.get('text', '')
        if date_str:
            try:
                d = dt.date.fromisoformat(date_str)
            except Exception:
                return JsonResponse({"error": "invalid date"}, status=400)
        else:
            d = _today_date()
        entry, created = JournalEntry.objects.update_or_create(user=user, date=d, defaults={"text": text})
        return JsonResponse({"date": d.isoformat(), "text": entry.text})


@login_required
def api_toggle_entry(request):
    """Toggle a habit entry for a specific date. Only allow toggling within the current month/year."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    user = request.user
    # log incoming raw body for debugging
    try:
        raw_body = request.body.decode()
        print(f"[api_toggle_entry] raw_body={raw_body}")
    except Exception:
        raw_body = None
    # Also log request meta for correlation (client request id, ua, ip)
    try:
        header_req_id = request.META.get('HTTP_X_REQUEST_ID')
        ua = request.META.get('HTTP_USER_AGENT')
        ip = request.META.get('REMOTE_ADDR')
        print(f"[api_toggle_entry] header_request_id={header_req_id} ua={ua} remote_addr={ip}")
    except Exception:
        pass
    data = request.POST or request.POST.copy()
    # support JSON body
    if not data:
        try:
            import json
            data = json.loads(request.body.decode())
        except Exception:
            data = {}
    habit_id = data.get('habit_id') or data.get('id')
    date_str = data.get('date')
    if not habit_id:
        return JsonResponse({"error": "habit_id required"}, status=400)
    try:
        habit = Habit.objects.get(id=int(habit_id), user=user)
    except Exception:
        return JsonResponse({"error": "habit not found"}, status=404)

    today = _today_date()
    if date_str:
        try:
            d = dt.date.fromisoformat(date_str)
        except Exception:
            return JsonResponse({"error": "invalid date format, use YYYY-MM-DD"}, status=400)
    else:
        d = today

    # Prevent editing past months: only allow toggling if date is within current month/year
    if not (d.year == today.year and d.month == today.month):
        return JsonResponse({"error": "Editing previous months is not allowed"}, status=403)

    try:
        entry, created = HabitEntry.objects.get_or_create(habit=habit, date=d, defaults={"completed": True, "user": user})
    except Exception as e:
        # try fallback to allow save() to populate user, but return clear error if it still fails
        try:
            entry, created = HabitEntry.objects.get_or_create(habit=habit, date=d, defaults={"completed": True})
        except Exception as e2:
            return JsonResponse({"error": "failed to toggle entry", "detail": str(e2)}, status=500)
    # Require explicit `completed` value from client to avoid toggle races.
    if isinstance(data, dict) and 'completed' in data:
        # capture any client-supplied request id for debugging
        request_id = data.get('request_id') or None
        if request_id:
            try:
                print(f"[api_toggle_entry] request_id={request_id}")
            except Exception:
                pass
        completed_val = data.get('completed')
        # normalize string values
        if isinstance(completed_val, str):
            completed_val = completed_val.lower() in ('1', 'true', 'yes', 'on')
        else:
            completed_val = bool(completed_val)
    else:
        return JsonResponse({"error": "`completed` parameter is required"}, status=400)

    # Set the explicit state idempotently
    entry.completed = completed_val
    entry.user = entry.user or user
    entry.save()
    # Build authoritative habit payload for the month containing `d`
    try:
        year = d.year
        month = d.month
        _, ndays = calendar.monthrange(year, month)
        entries = HabitEntry.objects.filter(habit=habit, date__year=year, date__month=month)
        entry_map = {e.date.day: e.completed for e in entries}
        days = []
        completed_count = 0
        for day in range(1, ndays + 1):
            completed = bool(entry_map.get(day, False))
            days.append({"day": day, "completed": completed})
            if completed:
                completed_count += 1
        pct = round((completed_count / ndays * 100), 1) if ndays else 0
        habit_payload = {"id": habit.id, "title": habit.title, "days": days, "completed_count": completed_count, "percentage": pct}
    except Exception:
        habit_payload = None

    # diagnostic log for debugging toggle behavior
    try:
        print(f"[api_toggle_entry] user={user.id} habit={habit.id} date={d.isoformat()} created={created} completed={entry.completed}")
    except Exception:
        pass

    resp = {"habit_id": habit.id, "date": d.isoformat(), "completed": entry.completed}
    if habit_payload is not None:
        resp["habit"] = habit_payload
    return JsonResponse(resp)

