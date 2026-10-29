from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from courses.models import Course, Section, Semester, TimeSlot
from enrollments.models import Enrollment
from enrollments.services import drop_student, enroll_student, is_enrollment_open

User = get_user_model()


class EnrollmentTestDataMixin:
    def setUp(self):
        self.user = User.objects.create_user(username="student1", password="Ntub-11356021!")
        self.profile = Profile.objects.create(user=self.user, student_id="S001", credit_limit=18)
        now = timezone.now()
        self.semester = Semester.objects.create(
            name="113-1",
            is_active=True,
            enroll_start=now - timedelta(days=1),
            enroll_end=now + timedelta(days=1),
        )
        self.course = Course.objects.create(code="CS101", name="程式設計", credits=3)
        self.section = Section.objects.create(
            course=self.course, semester=self.semester, capacity=2
        )
        TimeSlot.objects.create(
            section=self.section,
            weekday=1,
            start_time=time(9, 0),
            end_time=time(10, 0),
            location="A101",
        )

    def make_section(self, code="CS102", credits=3, capacity=2):
        course = Course.objects.create(code=code, name=f"課程 {code}", credits=credits)
        return Section.objects.create(course=course, semester=self.semester, capacity=capacity)

    def make_student(self, username):
        user = User.objects.create_user(username=username, password="Ntub-11356021!")
        Profile.objects.create(user=user, student_id=username.upper())
        return user

    def make_course_section(self, code="CS102", name=None, department="", teacher=None):
        course = Course.objects.create(
            code=code,
            name=name or f"課程 {code}",
            credits=3,
            department=department,
        )
        return Section.objects.create(
            course=course,
            semester=self.semester,
            capacity=10,
            teacher=teacher,
        )


class EnrollmentServiceTests(EnrollmentTestDataMixin, TestCase):
    def test_enroll_success(self):
        ok, msg = enroll_student(self.user, self.section)
        self.assertTrue(ok, msg)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)
        self.assertEqual(enrollment.status, Enrollment.Status.ENROLLED)

    def test_cannot_enroll_twice(self):
        enroll_student(self.user, self.section)
        ok, msg = enroll_student(self.user, self.section)
        self.assertFalse(ok)
        self.assertIn("已加選", msg)
        self.assertEqual(Enrollment.objects.filter(student=self.user, section=self.section).count(), 1)

    def test_cannot_reenroll_after_drop(self):
        enroll_student(self.user, self.section)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)
        drop_student(self.user, enrollment)

        ok, msg = enroll_student(self.user, self.section)

        self.assertFalse(ok)
        self.assertIn("不得重新加選", msg)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.DROPPED)
        self.assertEqual(Enrollment.objects.filter(student=self.user, section=self.section).count(), 1)

    def test_inactive_semester_blocks_enrollment(self):
        self.semester.is_active = False
        self.semester.save()
        ok, msg = enroll_student(self.user, self.section)
        self.assertFalse(ok)
        self.assertIn("非加選期間", msg)

    def test_enrollment_window_is_enforced(self):
        now = timezone.now()
        self.semester.enroll_start = now - timedelta(days=2)
        self.semester.enroll_end = now - timedelta(days=1)
        self.semester.save()
        self.assertFalse(is_enrollment_open(self.section))
        ok, _ = enroll_student(self.user, self.section)
        self.assertFalse(ok)

    def test_time_conflict_blocks_enrollment(self):
        self.assertTrue(enroll_student(self.user, self.section)[0])
        conflicting = self.make_section(code="CS102")
        TimeSlot.objects.create(
            section=conflicting,
            weekday=1,
            start_time=time(9, 30),
            end_time=time(10, 30),
        )
        ok, msg = enroll_student(self.user, conflicting)
        self.assertFalse(ok)
        self.assertIn("衝堂", msg)

    def test_non_overlapping_time_is_allowed(self):
        self.assertTrue(enroll_student(self.user, self.section)[0])
        other = self.make_section(code="CS102")
        TimeSlot.objects.create(
            section=other,
            weekday=1,
            start_time=time(10, 0),
            end_time=time(11, 0),
        )
        ok, msg = enroll_student(self.user, other)
        self.assertTrue(ok, msg)

    def test_credit_limit_is_enforced(self):
        self.profile.credit_limit = 3
        self.profile.save()
        self.assertTrue(enroll_student(self.user, self.section)[0])
        extra = self.make_section(code="CS102", credits=1)
        ok, msg = enroll_student(self.user, extra)
        self.assertFalse(ok)
        self.assertIn("學分上限", msg)

    def test_capacity_is_enforced(self):
        self.section.capacity = 1
        self.section.save()
        other = self.make_student("student2")
        self.assertTrue(enroll_student(self.user, self.section)[0])
        ok, msg = enroll_student(other, self.section)
        self.assertFalse(ok)
        self.assertIn("名額已滿", msg)

    def test_dropped_enrollment_does_not_occupy_capacity(self):
        self.section.capacity = 1
        self.section.save()
        enroll_student(self.user, self.section)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)
        self.assertTrue(drop_student(self.user, enrollment)[0])

        other = self.make_student("student2")
        ok, msg = enroll_student(other, self.section)
        self.assertTrue(ok, msg)

    def test_drop_requires_open_enrollment_window(self):
        enroll_student(self.user, self.section)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)
        self.semester.enroll_end = timezone.now() - timedelta(minutes=1)
        self.semester.save()

        ok, msg = drop_student(self.user, enrollment)

        self.assertFalse(ok)
        self.assertIn("非加退選期間", msg)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.ENROLLED)

    def test_cannot_drop_another_students_enrollment(self):
        enroll_student(self.user, self.section)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)
        other = self.make_student("student2")
        ok, msg = drop_student(other, enrollment)
        self.assertFalse(ok)
        self.assertIn("他人", msg)

    def test_drop_sets_status_and_timestamp(self):
        enroll_student(self.user, self.section)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)
        ok, msg = drop_student(self.user, enrollment)
        self.assertTrue(ok, msg)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.DROPPED)
        self.assertIsNotNone(enrollment.dropped_at)


class EnrollmentViewTests(EnrollmentTestDataMixin, TestCase):
    def test_course_list_requires_login(self):
        response = self.client.get(reverse("course_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_capacity_display_excludes_dropped_enrollments(self):
        self.client.login(username="student1", password="Ntub-11356021!")
        enroll_student(self.user, self.section)
        other = self.make_student("student2")
        Enrollment.objects.create(
            student=other, section=self.section, status=Enrollment.Status.DROPPED
        )

        response = self.client.get(reverse("course_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sections"][0].enrolled_count, 1)
        self.assertContains(response, "1/2")

    def test_course_list_shows_course_description(self):
        self.course.description = "基礎程式設計與除錯實作"
        self.course.save()
        self.client.login(username="student1", password="Ntub-11356021!")

        response = self.client.get(reverse("course_list"))

        self.assertContains(response, "基礎程式設計與除錯實作")

    def test_course_list_filters_by_keyword(self):
        self.make_course_section(code="BA101", name="管理學", department="企業管理系")
        self.client.login(username="student1", password="Ntub-11356021!")

        response = self.client.get(reverse("course_list"), {"q": "CS101"})

        self.assertEqual([s.course.code for s in response.context["sections"]], ["CS101"])
        self.assertContains(response, "CS101")
        self.assertNotContains(response, "BA101")
        self.assertContains(response, "關鍵字「CS101」")

    def test_course_list_filters_by_department(self):
        self.make_course_section(code="BA101", name="管理學", department="企業管理系")
        self.make_course_section(code="IM101", name="程式設計", department="資訊管理系")
        self.client.login(username="student1", password="Ntub-11356021!")

        response = self.client.get(
            reverse("course_list"), {"department": "企業管理系"}
        )

        self.assertEqual([s.course.code for s in response.context["sections"]], ["BA101"])
        self.assertContains(response, "系所「企業管理系」")

    def test_course_list_filters_by_teacher_name(self):
        teacher = User.objects.create_user(
            username="wang.cs", first_name="王大明", password="Ntub-11356021!"
        )
        self.make_course_section(code="BA101", name="管理學", teacher=teacher)
        self.client.login(username="student1", password="Ntub-11356021!")

        response = self.client.get(reverse("course_list"), {"q": "王大明"})

        self.assertEqual([s.course.code for s in response.context["sections"]], ["BA101"])

    def test_course_list_shows_empty_message_when_no_match(self):
        self.client.login(username="student1", password="Ntub-11356021!")

        response = self.client.get(reverse("course_list"), {"q": "不存在的課程"})

        self.assertEqual(len(response.context["sections"]), 0)
        self.assertContains(response, "找不到符合條件的課程")

    def test_dropped_section_shows_no_enroll_button(self):
        self.client.login(username="student1", password="Ntub-11356021!")
        enroll_student(self.user, self.section)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)
        drop_student(self.user, enrollment)

        response = self.client.get(reverse("course_list"))

        self.assertContains(response, "已退選")
        self.assertNotContains(response, reverse("enroll", args=[self.section.id]))

    def test_reenroll_via_view_is_rejected(self):
        self.client.login(username="student1", password="Ntub-11356021!")
        enroll_student(self.user, self.section)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)
        drop_student(self.user, enrollment)

        response = self.client.post(
            reverse("enroll", args=[self.section.id]), follow=True
        )

        self.assertContains(response, "不得重新加選")
        self.assertEqual(
            Enrollment.objects.filter(student=self.user, section=self.section).count(), 1
        )

    def test_drop_view_updates_enrollment(self):
        self.client.login(username="student1", password="Ntub-11356021!")
        enroll_student(self.user, self.section)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)

        response = self.client.post(reverse("drop", args=[enrollment.id]))

        self.assertRedirects(response, reverse("my_schedule"))
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.DROPPED)

    def test_my_schedule_shows_credit_summary(self):
        self.client.login(username="student1", password="Ntub-11356021!")
        enroll_student(self.user, self.section)

        response = self.client.get(reverse("my_schedule"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_credits"], 3)
        self.assertEqual(response.context["remaining_credits"], 15)
        self.assertContains(response, "剩餘學分")

    def test_my_schedule_builds_weekly_grid(self):
        self.client.login(username="student1", password="Ntub-11356021!")
        enroll_student(self.user, self.section)

        response = self.client.get(reverse("my_schedule"))

        grid = response.context["grid"]
        self.assertEqual(len(grid), 1)
        self.assertEqual(len(grid[0]["cells"]), 7)
        monday = grid[0]["cells"][0]
        self.assertEqual(len(monday), 1)
        self.assertEqual(monday[0]["enrollment"].section.course.code, "CS101")
        self.assertContains(response, "週一")
        self.assertContains(response, "CS101")

    def test_my_schedule_grid_is_empty_without_enrollments(self):
        self.client.login(username="student1", password="Ntub-11356021!")

        response = self.client.get(reverse("my_schedule"))

        self.assertEqual(response.context["grid"], [])
        self.assertContains(response, "尚未選課")

    def test_history_lists_dropped_enrollments(self):
        self.client.login(username="student1", password="Ntub-11356021!")
        enroll_student(self.user, self.section)
        enrollment = Enrollment.objects.get(student=self.user, section=self.section)
        drop_student(self.user, enrollment)

        response = self.client.get(reverse("enrollment_history"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "已退選")
        self.assertContains(response, self.course.code)
        self.assertEqual(response.context["dropped_count"], 1)
