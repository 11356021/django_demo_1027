from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "student_id", "credit_limit")
    list_filter = ("role",)
    search_fields = ("user__username", "student_id")
