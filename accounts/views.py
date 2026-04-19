from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import LoginForm, OTPVerifyForm, StudentEmailForm
from .models import StudentOTP, User


# 🔐 Login
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("events:home")

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("events:home")

    return render(request, "accounts/login.html", {"form": form})


# 🔓 Logout
@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("events:home")


# 📧 Step 1: Email → OTP
def student_signup_request_otp(request: HttpRequest) -> HttpResponse:
    form = StudentEmailForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        full_name = form.cleaned_data["full_name"].strip()

        otp = StudentOTP.create_for_email(email)

        print("OTP:", otp.code)

        send_mail(
            subject="Your OTP Code",
            message=f"Your OTP is: {otp.code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        messages.success(request, "OTP sent. Check your email and the server console for the code.")
        request.session["signup_data"] = {"email": email, "full_name": full_name}

        verify_url = reverse("accounts:verify_otp")
        return redirect(f"{verify_url}?email={email}")

    return render(request, "accounts/student_signup.html", {"form": form})


# 🔢 Step 2: OTP Verify
def verify_otp(request: HttpRequest) -> HttpResponse:
    signup_data = request.session.get("signup_data", {})
    email = signup_data.get("email") or request.GET.get("email", "")
    full_name = signup_data.get("full_name", "")

    form = OTPVerifyForm(initial={"email": email})

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)

        if form.is_valid():
            otp = form.cleaned_data["otp_obj"]
            email = form.cleaned_data["email"]

            otp.used_at = timezone.now()
            otp.save()

            username = email.split("@")[0]
            first_name, _, last_name = full_name.partition(" ")

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": User.Role.STUDENT,
                },
            )

            if created and full_name:
                user.first_name = first_name
                user.last_name = last_name
                user.save(update_fields=["first_name", "last_name"])

            login(request, user)
            request.session.pop("signup_data", None)

            return redirect("events:home")

    return render(request, "accounts/student_verify.html", {"form": form, "email": email, "full_name": full_name})