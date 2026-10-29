from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile

User = get_user_model()

PASSWORD = "Ntub-11356021!"


class RegistrationTests(TestCase):
    def test_register_creates_student_profile_and_logs_in(self):
        response = self.client.post(reverse("register"), {
            "username": "newstudent",
            "student_id": "S123",
            "email": "new@example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
        })

        self.assertRedirects(response, reverse("course_list"))
        user = User.objects.get(username="newstudent")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.profile.student_id, "S123")
        self.assertEqual(user.profile.role, Profile.Role.STUDENT)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_duplicate_student_id_is_rejected(self):
        other = User.objects.create_user(username="other", password=PASSWORD)
        Profile.objects.create(user=other, student_id="S123")

        response = self.client.post(reverse("register"), {
            "username": "newstudent",
            "student_id": "S123",
            "password1": PASSWORD,
            "password2": PASSWORD,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "此學號已被註冊")
        self.assertFalse(User.objects.filter(username="newstudent").exists())

    def test_register_page_redirects_authenticated_users(self):
        user = User.objects.create_user(username="student", password=PASSWORD)
        Profile.objects.create(user=user, student_id="S001")
        self.client.login(username="student", password=PASSWORD)

        response = self.client.get(reverse("register"))

        self.assertRedirects(response, reverse("course_list"))


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student", email="old@example.com", password=PASSWORD
        )
        self.profile = Profile.objects.create(
            user=self.user, student_id="S001", credit_limit=20
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_profile_displays_student_data(self):
        self.client.login(username="student", password=PASSWORD)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "S001")
        self.assertContains(response, "20")
        self.assertContains(response, "學生")

    def test_profile_creates_missing_profile_for_staff(self):
        admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password=PASSWORD
        )
        self.client.login(username="admin", password=PASSWORD)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        created = Profile.objects.get(user=admin)
        self.assertEqual(created.role, Profile.Role.ADMIN)

    def test_profile_can_be_updated(self):
        self.client.login(username="student", password=PASSWORD)

        response = self.client.post(reverse("profile"), {
            "student_id": "S999",
            "email": "new@example.com",
        }, follow=True)

        self.assertContains(response, "個人資料已更新")
        self.profile.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.profile.student_id, "S999")
        self.assertEqual(self.user.email, "new@example.com")

    def test_profile_rejects_student_id_used_by_another_user(self):
        other = User.objects.create_user(username="other", password=PASSWORD)
        Profile.objects.create(user=other, student_id="S999")
        self.client.login(username="student", password=PASSWORD)

        response = self.client.post(reverse("profile"), {
            "student_id": "S999",
            "email": "new@example.com",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "已被其他帳號使用")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.student_id, "S001")

    def test_empty_student_id_is_allowed(self):
        self.client.login(username="student", password=PASSWORD)

        response = self.client.post(reverse("profile"), {
            "student_id": "",
            "email": "new@example.com",
        })

        self.assertRedirects(response, reverse("profile"))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.student_id, "")


class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student", email="student@example.com", password=PASSWORD
        )
        self.client.login(username="student", password=PASSWORD)

    def test_password_change_page_uses_site_template(self):
        response = self.client.get(reverse("password_change"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_change_form.html")
        self.assertContains(response, "修改密碼")
        self.assertNotContains(response, 'name="old_password"')

    def test_password_can_be_changed_without_old_password(self):
        response = self.client.post(reverse("password_change"), {
            "new_password1": "NewPass-2026!",
            "new_password2": "NewPass-2026!",
        })

        self.assertRedirects(response, reverse("password_change_done"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass-2026!"))
        self.assertTemplateUsed(
            self.client.get(reverse("password_change_done")),
            "registration/password_change_done.html",
        )


@override_settings(MAILERS={
    "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
})
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student", email="student@example.com", password=PASSWORD
        )
        mail.outbox = []

    def test_password_reset_page_uses_site_template(self):
        response = self.client.get(reverse("password_reset"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_form.html")
        self.assertContains(response, "忘記密碼")

    def test_password_reset_sends_site_email(self):
        response = self.client.post(
            reverse("password_reset"), {"email": "student@example.com"}
        )

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["student@example.com"])
        self.assertIn("密碼重設", message.subject)
        self.assertIn("/accounts/reset/", message.body)

    def test_password_reset_confirm_and_complete_flow(self):
        self.client.post(reverse("password_reset"), {"email": "student@example.com"})
        reset_path = next(
            part for part in mail.outbox[0].body.split()
            if part.startswith("http://testserver/accounts/reset/")
        )
        response = self.client.get(reset_path, follow=True)
        self.assertContains(response, "設定新密碼")

        response = self.client.post(response.request["PATH_INFO"], {
            "new_password1": "NewPass-2026!",
            "new_password2": "NewPass-2026!",
        })

        self.assertRedirects(response, reverse("password_reset_complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass-2026!"))
