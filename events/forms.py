from __future__ import annotations

from django import forms
from django.utils import timezone

from accounts.models import User

from .models import Event, Feedback


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "rules",
            "duration_minutes",
            "category",
            "venue",
            "start_at",
            "registration_deadline",
            "capacity",
            "poster",
            "organizer",
            "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control form-control-dark"}),
            "description": forms.Textarea(attrs={"class": "form-control form-control-dark", "rows": 4}),
            "rules": forms.Textarea(attrs={"class": "form-control form-control-dark", "rows": 4, "placeholder": "Add event rules or guidelines..."}),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control form-control-dark", "min": 1, "placeholder": "Minutes"}),
            "venue": forms.TextInput(attrs={"class": "form-control form-control-dark"}),
            "start_at": forms.DateTimeInput(attrs={"class": "form-control form-control-dark", "type": "datetime-local"}),
            "registration_deadline": forms.DateTimeInput(attrs={"class": "form-control form-control-dark", "type": "datetime-local"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control form-control-dark", "min": 1}),
            "poster": forms.ClearableFileInput(attrs={"class": "form-control form-control-dark"}),
            "organizer": forms.Select(attrs={"class": "form-select form-select-dark"}),
            "is_published": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organizer"].queryset = User.objects.filter(role=User.Role.ORGANIZER).order_by("username")
        self.fields["organizer"].required = False

    def clean(self):
        cleaned = super().clean()
        start_at = cleaned.get("start_at")
        deadline = cleaned.get("registration_deadline")
        if start_at and deadline and deadline > start_at:
            self.add_error("registration_deadline", "Deadline must be before event start time.")
        if deadline and deadline < timezone.now() - timezone.timedelta(days=1):
            self.add_error("registration_deadline", "Deadline looks too far in the past.")
        return cleaned


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Optional feedback"}),
        }


class RegistrationForm(forms.Form):
    YEAR_CHOICES = [
        ("1", "1st year"),
        ("2", "2nd year"),
        ("3", "3rd year"),
        ("4", "4th year"),
        ("Other", "Other"),
    ]

    name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Your full name"}),
    )
    phone = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Contact phone number"}),
    )
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    department = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Department"}),
    )

