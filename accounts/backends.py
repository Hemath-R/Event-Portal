from __future__ import annotations

from django.conf import settings
from django.contrib.auth.backends import ModelBackend

from .models import User


class DevAnyPasswordBackend(ModelBackend):
    """
    Development-only backend:
    - Allows login with any password.
    - Auto-creates a STUDENT user if username/email doesn't exist.
    Enabled only when DEBUG=True via AUTHENTICATION_BACKENDS.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not settings.DEBUG:
            return None

        raw = (username or kwargs.get("email") or "").strip()
        if not raw:
            return None

        user = None
        if "@" in raw:
            user = User.objects.filter(email=raw.lower()).first()
            if not user:
                uname = raw.split("@")[0]
                user = User.objects.create_user(
                    username=uname,
                    email=raw.lower(),
                    password=password or "dev",
                    role=User.Role.STUDENT,
                )
        else:
            user = User.objects.filter(username=raw).first()
            if not user:
                user = User.objects.create_user(
                    username=raw,
                    email = f"{raw}@rgcet.edu.in",
                    password=password or "dev",
                    role=User.Role.STUDENT,
                )

        if user and self.user_can_authenticate(user):
            return user
        return None

