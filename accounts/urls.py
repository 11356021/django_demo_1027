from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import PasswordChangeWithoutOldForm

urlpatterns = [
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            form_class=PasswordChangeWithoutOldForm
        ),
        name="password_change",
    ),
]
