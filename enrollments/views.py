from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from courses.models import Section, Semester
from enrollments.models import Enrollment
from enrollments.services import enroll_student, drop_student


@login_required
def course_list(request):
    semester_id = request.GET.get("semester")
    semesters = Semester.objects.all().order_by("-name")
    if semester_id:
        semester = get_object_or_404(Semester, pk=semester_id)
    else:
        semester = semesters.filter(is_active=True).first() or semesters.first()
    sections = Section.objects.filter(semester=semester).select_related("course", "teacher").prefetch_related("timeslots") if semester else []
    enrolled_section_ids = set(
        Enrollment.objects.filter(student=request.user, status=Enrollment.Status.ENROLLED).values_list("section_id", flat=True)
    )
    return render(request, "enrollments/course_list.html", {
        "semesters": semesters,
        "semester": semester,
        "sections": sections,
        "enrolled_section_ids": enrolled_section_ids,
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
    enrollments = (
        Enrollment.objects.filter(student=request.user, status=Enrollment.Status.ENROLLED)
        .select_related("section__course", "section__semester", "section__teacher")
        .prefetch_related("section__timeslots")
    )
    return render(request, "enrollments/my_schedule.html", {"enrollments": enrollments})
