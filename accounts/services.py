from .models import Profile

DEFAULT_CREDIT_LIMIT = 18


def get_or_create_profile(user):
    """Return the user's profile.

    Profiles are not created automatically elsewhere, so pages must use this
    helper instead of assuming ``user.profile`` exists. Staff accounts get the
    admin role; everyone else starts as a student.
    """
    role = Profile.Role.ADMIN if user.is_staff else Profile.Role.STUDENT
    profile, _ = Profile.objects.get_or_create(user=user, defaults={"role": role})
    return profile


def get_credit_limit(user):
    profile = getattr(user, "profile", None)
    return profile.credit_limit if profile else DEFAULT_CREDIT_LIMIT
