from django.core.exceptions import ValidationError

MAX_PROFILE_PICTURE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_profile_picture_size(file):
    """Django's ImageField already verifies the upload is a real image (via
    Pillow) and rejects disguised files, but it has no size limit of its
    own - without this, an authenticated user could upload arbitrarily
    large files and exhaust storage."""
    if file.size > MAX_PROFILE_PICTURE_SIZE_BYTES:
        max_mb = MAX_PROFILE_PICTURE_SIZE_BYTES // (1024 * 1024)
        raise ValidationError(f"Image file too large. Maximum size is {max_mb}MB.")
