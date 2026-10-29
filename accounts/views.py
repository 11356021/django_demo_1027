from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileForm, StudentRegistrationForm
from .services import get_or_create_profile


def register(request):
    if request.user.is_authenticated:
        return redirect("course_list")
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "註冊成功，歡迎使用選課系統。")
            return redirect("course_list")
    else:
        form = StudentRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    user_profile = get_or_create_profile(request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, user=request.user, profile=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "個人資料已更新。")
            return redirect("profile")
    else:
        form = ProfileForm(user=request.user, profile=user_profile)
    return render(request, "accounts/profile.html", {"profile": user_profile, "form": form})
