from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


def upload_event_poster_to(instance: "Event", filename: str) -> str:
    return f"events/{instance.id or 'new'}/poster/{filename}"


class Event(models.Model):
    class Category(models.TextChoices):
        TECH = "TECH", "Tech"
        NON_TECH = "NON_TECH", "Non-tech"
        SPORTS = "SPORTS", "Sports"
        CULTURAL = "CULTURAL", "Cultural"
        WORKSHOP = "WORKSHOP", "Workshop"

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="events_created",
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="events_organized",
        null=True,
        blank=True,
        help_text="Optional organizer assigned by Admin.",
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    rules = models.TextField(blank=True, default="")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Optional event time limit in minutes.")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.TECH)
    venue = models.CharField(max_length=200)
    start_at = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=50)
    poster = models.ImageField(upload_to=upload_event_poster_to, null=True, blank=True)

    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_at", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def is_registration_open(self) -> bool:
        return self.is_published and timezone.now() <= self.registration_deadline

    def seats_left(self) -> int:
        count = self.registrations.filter(status__in=[Registration.Status.PENDING, Registration.Status.COMPLETED]).count()
        return max(0, int(self.capacity) - count)


class Registration(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="registrations")
    name = models.CharField(max_length=200, default="", blank=True)
    phone = models.CharField(max_length=20, default="", blank=True)
    year = models.CharField(max_length=20, default="", blank=True)
    department = models.CharField(max_length=100, default="", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("event", "student")]
        indexes = [models.Index(fields=["event", "student"])]

    def __str__(self) -> str:
        return f"{self.student} -> {self.event}"


class Attendance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attendance")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance")
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="attendance_marked",
    )
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("event", "student")]
        indexes = [models.Index(fields=["event", "student"])]

    def __str__(self) -> str:
        return f"Attendance({self.event_id}, {self.student_id})"


class Feedback(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="feedback")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedback")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("event", "student")]
        indexes = [models.Index(fields=["event", "created_at"])]

    def __str__(self) -> str:
        return f"Feedback({self.event_id}, {self.student_id}, {self.rating})"
