from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm

from .models import Profile

User = get_user_model()


class StudentRegistrationForm(UserCreationForm):
    student_id = forms.CharField(label="學號", max_length=20)
    email = forms.EmailField(label="Email", required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "帳號"
        self.fields["password1"].label = "密碼"
        self.fields["password2"].label = "確認密碼"
        self.order_fields(["username", "student_id", "email", "password1", "password2"])

    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"].strip()
        if Profile.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError("此學號已被註冊。")
        return student_id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "role": Profile.Role.STUDENT,
                    "student_id": self.cleaned_data["student_id"],
                },
            )
        return user


class ProfileForm(forms.Form):
    student_id = forms.CharField(label="學號", max_length=20, required=False)
    email = forms.EmailField(label="Email", required=False)

    def __init__(self, *args, user, profile, **kwargs):
        self.user = user
        self.profile = profile
        super().__init__(*args, **kwargs)
        self.fields["student_id"].initial = profile.student_id
        self.fields["email"].initial = user.email

    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"].strip()
        if student_id and (
            Profile.objects.filter(student_id=student_id).exclude(user=self.user).exists()
        ):
            raise forms.ValidationError("此學號已被其他帳號使用。")
        return student_id

    def save(self):
        self.profile.student_id = self.cleaned_data["student_id"]
        self.profile.save(update_fields=["student_id"])
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["email"])
        return self.profile


class PasswordChangeWithoutOldForm(SetPasswordForm):
    """修改密碼時不要求輸入舊密碼。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control",
                "autocomplete": "new-password",
            })
        self.fields["new_password1"].label = "新密碼"
        self.fields["new_password2"].label = "確認新密碼"
