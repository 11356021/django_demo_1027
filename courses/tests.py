from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .models import Course, Section, Semester, TimeSlot


class SeedDemoCommandTests(TestCase):
    def run_seed(self):
        call_command("seed_demo", stdout=StringIO())

    def test_seed_is_idempotent_and_fills_descriptions(self):
        self.run_seed()
        first = (
            Course.objects.count(),
            Section.objects.count(),
            TimeSlot.objects.count(),
        )
        self.assertGreaterEqual(Course.objects.count(), 10)
        self.assertEqual(
            Course.objects.exclude(description="").count(), Course.objects.count()
        )
        self.assertTrue(Semester.objects.get(name="115-1").is_active)

        self.run_seed()

        second = (
            Course.objects.count(),
            Section.objects.count(),
            TimeSlot.objects.count(),
        )
        self.assertEqual(first, second)
