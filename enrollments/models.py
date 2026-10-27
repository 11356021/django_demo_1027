from django.conf import settings
from django.db import models

from courses.models import Section


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = "ENROLLED", "Enrolled"
        DROPPED = "DROPPED", "Dropped"

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ENROLLED)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    dropped_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student", "section")

    def __str__(self):
        return f"{self.student.username} - {self.section} [{self.status}]"
