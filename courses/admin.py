from django.contrib import admin

from .models import Course, Section, Semester, TimeSlot


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "enroll_start", "enroll_end")
    list_filter = ("is_active",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "credits", "department")
    search_fields = ("code", "name")


class TimeSlotInline(admin.TabularInline):
    model = TimeSlot
    extra = 1


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("course", "semester", "teacher", "capacity")
    list_filter = ("semester",)
    search_fields = ("course__code", "course__name")
    inlines = [TimeSlotInline]
