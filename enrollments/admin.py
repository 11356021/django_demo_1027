from django.contrib import admin

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "section", "status", "enrolled_at", "dropped_at")
    list_filter = ("status", "section__semester")
    search_fields = ("student__username", "section__course__code")
