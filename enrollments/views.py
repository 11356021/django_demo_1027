from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.services import get_or_create_profile
from courses.models import Section, Semester, TimeSlot
from enrollments.models import Enrollment
from enrollments.services import enroll_student, drop_student

WEEKDAYS = list(TimeSlot.WEEKDAY_LABELS.items())


def build_week_grid(enrollments):
    enrollment_slots = [
        (enrollment, slot)
        for enrollment in enrollments
        for slot in enrollment.section.timeslots.all()
    ]
    time_rows = sorted({(slot.start_time, slot.end_time) for _, slot in enrollment_slots})
    grid = []
    for start_time, end_time in time_rows:
        cells = []
        for weekday, _label in WEEKDAYS:
            cells.append([
                {"enrollment": enrollment, "slot": slot}
                for enrollment, slot in enrollment_slots
                if slot.weekday == weekday
                and slot.start_time == start_time
                and slot.end_time == end_time
            ])
        grid.append({"start_time": start_time, "end_time": end_time, "cells": cells})
    return grid


@login_required
def course_list(request):
    semester_id = request.GET.get("semester")
    keyword = request.GET.get("q", "").strip()
    department = request.GET.get("department", "").strip()
    semesters = Semester.objects.all().order_by("-name")
    if semester_id:
        semester = get_object_or_404(Semester, pk=semester_id)
    else:
        semester = semesters.filter(is_active=True).first() or semesters.first()
    sections = (
        Section.objects.filter(semester=semester)
        .select_related("course", "teacher")
        .prefetch_related("timeslots")
        .annotate(
            enrolled_count=Count(
                "enrollments",
                filter=Q(enrollments__status=Enrollment.Status.ENROLLED),
            )
        )
        .order_by("course__code")
        if semester
        else Section.objects.none()
    )
    departments = list(
        sections.exclude(course__department="")
        .values_list("course__department", flat=True)
        .distinct()
        .order_by("course__department")
    )
    if keyword:
        sections = sections.filter(
            Q(course__code__icontains=keyword)
            | Q(course__name__icontains=keyword)
            | Q(course__description__icontains=keyword)
            | Q(teacher__username__icontains=keyword)
            | Q(teacher__first_name__icontains=keyword)
            | Q(teacher__last_name__icontains=keyword)
        )
    if department:
        sections = sections.filter(course__department=department)
    statuses = list(
        Enrollment.objects.filter(student=request.user).values_list("section_id", "status")
    )
    enrolled_section_ids = {
        section_id for section_id, status in statuses if status == Enrollment.Status.ENROLLED
    }
    dropped_section_ids = {
        section_id for section_id, status in statuses if status == Enrollment.Status.DROPPED
    }
    return render(request, "enrollments/course_list.html", {
        "semesters": semesters,
        "semester": semester,
        "sections": sections,
        "departments": departments,
        "keyword": keyword,
        "selected_department": department,
        "has_filters": bool(keyword or department),
        "enrolled_section_ids": enrolled_section_ids,
        "dropped_section_ids": dropped_section_ids,
    })


@login_required
def enroll(request, section_id):
    if request.method != "POST":
        return redirect("course_list")
    section = get_object_or_404(Section, pk=section_id)
    ok, msg = enroll_student(request.user, section)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect("course_list")


@login_required
def drop(request, enrollment_id):
    if request.method != "POST":
        return redirect("my_schedule")
    enrollment = get_object_or_404(Enrollment, pk=enrollment_id)
    ok, msg = drop_student(request.user, enrollment)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect("my_schedule")


@login_required
def my_schedule(request):
    enrollments = list(
        Enrollment.objects.filter(student=request.user, status=Enrollment.Status.ENROLLED)
        .select_related("section__course", "section__semester", "section__teacher")
        .prefetch_related("section__timeslots")
        .order_by("section__course__code")
    )
    total_credits = sum(enrollment.section.course.credits for enrollment in enrollments)
    credit_limit = get_or_create_profile(request.user).credit_limit
    return render(request, "enrollments/my_schedule.html", {
        "enrollments": enrollments,
        "course_count": len(enrollments),
        "total_credits": total_credits,
        "credit_limit": credit_limit,
        "remaining_credits": credit_limit - total_credits,
        "weekdays": WEEKDAYS,
        "grid": build_week_grid(enrollments),
    })


@login_required
def enrollment_history(request):
    enrollments = (
        Enrollment.objects.filter(student=request.user)
        .select_related("section__course", "section__semester", "section__teacher")
        .prefetch_related("section__timeslots")
        .order_by("-enrolled_at")
    )
    return render(request, "enrollments/history.html", {
        "enrollments": enrollments,
        "enrolled_count": enrollments.filter(status=Enrollment.Status.ENROLLED).count(),
        "dropped_count": enrollments.filter(status=Enrollment.Status.DROPPED).count(),
    })
