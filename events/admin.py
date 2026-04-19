from django.contrib import admin

from .models import Attendance, Event, Feedback, Registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "start_at", "venue", "capacity", "registration_deadline", "is_published", "organizer")
    list_filter = ("is_published",)
    search_fields = ("title", "venue")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("event", "student", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("student__username", "student__email", "event__title")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("event", "student", "marked_by", "marked_at")
    search_fields = ("student__username", "student__email", "event__title")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("event", "student", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("student__username", "student__email", "event__title")
