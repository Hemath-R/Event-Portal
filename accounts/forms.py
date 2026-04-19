from __future__ import annotations

import os
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import StudentOTP, User


# 🔐 Login Form
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control form-control-dark"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-dark"})
    )


class AdminLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control form-control-dark", "placeholder": "hemath"}),
        label="Admin username",
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-dark", "placeholder": "Enter admin password (optional)"}),
        label="Admin password",
    )


# 📧 Email Form (OTP send)
class StudentEmailForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-dark",
            "placeholder": "Jane Doe"
        }),
        label="Full name",
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control form-control-dark",
            "placeholder": "yourname@example.com"
        }),
        label="Email address",
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower().strip()
        return email


# 🔢 OTP Verify Form
class OTPVerifyForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-dark",
            "placeholder": "6-digit OTP"
        }),
    )

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").lower().strip()
        code = (cleaned.get("code") or "").strip()

        if not email or not code:
            return cleaned

        otp = StudentOTP.objects.filter(email=email).order_by("-created_at").first()

        if not otp or otp.is_used:
            raise ValidationError("OTP not found. Please request a new OTP.")

        if otp.is_expired():
            raise ValidationError("OTP expired. Please request a new OTP.")

        if otp.code != code:
            raise ValidationError("Invalid OTP.")

        cleaned["otp_obj"] = otp
        return cleaned