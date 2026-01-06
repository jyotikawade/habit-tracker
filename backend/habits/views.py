from django.shortcuts import render, redirect
from .models import Habit
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    habits = Habit.objects.filter(user=request.user)
    return render(request, "home.html", {"habits": habits})

@login_required
def add_habit(request):
    if request.method == "POST":
        title = request.POST['title']
        Habit.objects.create(user=request.user, title=title)
        return redirect("home")
    return render(request, "add_habit.html")

@login_required
def toggle_habit(request, id):
    habit = Habit.objects.get(id=id)
    habit.completed = not habit.completed
    habit.save()
    return redirect("home")
