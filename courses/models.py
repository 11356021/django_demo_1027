from django.conf import settings
from django.db import models


class Semester(models.Model):
    name = models.CharField(max_length=20, unique=True)  # e.g. 113-1
    is_active = models.BooleanField(default=False)
    enroll_start = models.DateTimeField(null=True, blank=True)
    enroll_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    credits = models.PositiveIntegerField()
    department = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("code",)

    def __str__(self):
        return f"{self.code} {self.name}"


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="sections")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="teaching_sections")
    capacity = models.PositiveIntegerField(default=40)

    class Meta:
        unique_together = ("course", "semester")

    def __str__(self):
        return f"{self.course.code}-{self.semester.name}"


class TimeSlot(models.Model):
    WEEKDAY_CHOICES = [
        (1, "Monday"),
        (2, "Tuesday"),
        (3, "Wednesday"),
        (4, "Thursday"),
        (5, "Friday"),
        (6, "Saturday"),
        (7, "Sunday"),
    ]

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="timeslots")
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.section} {self.get_weekday_display()} {self.start_time}-{self.end_time}"
