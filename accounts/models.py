from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ORGANIZER = "ORGANIZER", "Organizer"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_organizer(self) -> bool:
        return self.role == self.Role.ORGANIZER

    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT


class StudentOTP(models.Model):
    email = models.EmailField(db_index=True)
    code = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["email", "-created_at"]),
        ]

    @property
    def is_used(self) -> bool:
        return self.used_at is not None

    def is_expired(self) -> bool:
        return timezone.now() > self.created_at + timedelta(minutes=10)

    @classmethod
    def create_for_email(cls, email: str) -> "StudentOTP":
        code = str(secrets.randbelow(900000) + 100000)
        return cls.objects.create(email=email.lower().strip(), code=code)


def upload_organizer_signature_to(instance: "OrganizerProfile", filename: str) -> str:
    return f"organizers/{instance.user_id}/signature/{filename}"


class OrganizerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organizer_profile")
    signature_image = models.ImageField(upload_to=upload_organizer_signature_to, blank=True, null=True)
