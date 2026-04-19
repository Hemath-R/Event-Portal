from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from .models import User

F = TypeVar("F", bound=Callable[..., HttpResponse])


def role_required(*roles: str):
    def decorator(view_func: F) -> F:
        @login_required
        @wraps(view_func)
        def _wrapped(request: HttpRequest, *args, **kwargs):
            user: User = request.user  # type: ignore[assignment]
            if user.is_superuser or user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission to access that page.")
            return redirect("events:home")

        return _wrapped  # type: ignore[return-value]

    return decorator

