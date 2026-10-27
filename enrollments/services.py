from datetime import datetime

from django.db.models import Sum
from django.utils import timezone

from courses.models import Section, TimeSlot
from enrollments.models import Enrollment


def times_overlap(ts1_start, ts1_end, ts2_start, ts2_end):
    return ts1_start < ts2_end and ts2_start < ts1_end


def has_time_conflict(student, section):
    # get all enrolled sections' timeslots for this student
    enrolled_sections = Section.objects.filter(
        enrollments__student=student,
        enrollments__status=Enrollment.Status.ENROLLED,
    ).distinct()
    new_slots = TimeSlot.objects.filter(section=section)
    for es in enrolled_sections:
        for es_slot in TimeSlot.objects.filter(section=es):
            for ns in new_slots:
                if es_slot.weekday == ns.weekday and times_overlap(es_slot.start_time, es_slot.end_time, ns.start_time, ns.end_time):
                    return True
    return False


def would_exceed_credit_limit(student, section):
    profile = getattr(student, "profile", None)
    limit = profile.credit_limit if profile else 18
    current = Enrollment.objects.filter(student=student, status=Enrollment.Status.ENROLLED).aggregate(
        total=Sum("section__course__credits")
    )["total"] or 0
    return current + section.course.credits > limit


def is_enrollment_open(section):
    sem = section.semester
    if not sem.is_active:
        return False
    now = timezone.now()
    if sem.enroll_start and now < sem.enroll_start:
        return False
    if sem.enroll_end and now > sem.enroll_end:
        return False
    return True


def enroll_student(student, section):
    if Enrollment.objects.filter(student=student, section=section, status=Enrollment.Status.ENROLLED).exists():
        return False, "Already enrolled."
    if not is_enrollment_open(section):
        return False, "Enrollment not open for this semester."
    if has_time_conflict(student, section):
        return False, "Time conflict with existing enrolled course."
    if would_exceed_credit_limit(student, section):
        return False, "Exceeds credit limit."
    count_enrolled = Enrollment.objects.filter(section=section, status=Enrollment.Status.ENROLLED).count()
    if count_enrolled >= section.capacity:
        return False, "Section is full."
    Enrollment.objects.create(student=student, section=section, status=Enrollment.Status.ENROLLED)
    return True, "Enrolled successfully."


def drop_student(student, enrollment):
    if enrollment.student_id != student.id:
        return False, "Not allowed."
    if enrollment.status != Enrollment.Status.ENROLLED:
        return False, "Already dropped."
    enrollment.status = Enrollment.Status.DROPPED
    enrollment.dropped_at = timezone.now()
    enrollment.save()
    return True, "Dropped successfully."
