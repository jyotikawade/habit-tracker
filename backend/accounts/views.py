from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

def signup_view(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = User.objects.create_user(username=email, email=email, password=password)
        user.save()
        return redirect("login")
    return render(request, "signup.html")


def logout_view(request):
    logout(request)
    return redirect("login")

def login_view(request):
    message = ""
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)
            # Redirect to home
            return redirect("home")
        else:
            message = "Invalid email or password. Try again."

    return render(request, "login.html", {"message": message})
