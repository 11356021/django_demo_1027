from django.conf import settings
from django.db import models


class Profile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        TEACHER = "TEACHER", "Teacher"
        ADMIN = "ADMIN", "Admin"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    student_id = models.CharField(max_length=20, blank=True)
    credit_limit = models.PositiveIntegerField(default=18)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
