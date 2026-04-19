from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
   path("home/", views.home, name="home"),
    path("events/", views.event_list, name="event_list"),
    path("events/<int:event_id>/", views.event_detail, name="event_detail"),
    path("events/<int:event_id>/register/", views.register_for_event, name="register"),
    path("my/registrations/", views.my_registrations, name="my_registrations"),
    path("certificate/verify/<str:certificate_id>/", views.verify_certificate, name="verify_certificate"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("organizer/events/", views.organizer_events, name="organizer_events"),
    path("organizer/events/<int:event_id>/attendance/", views.attendance_mark, name="attendance"),
    path("events/<int:event_id>/certificate/preview/", views.certificate_preview, name="certificate_preview"),
    path("events/<int:event_id>/certificate/", views.download_certificate, name="certificate"),
    path("events/<int:event_id>/feedback/", views.leave_feedback, name="feedback"),
    path("organizer/events/<int:event_id>/feedback-summary/", views.feedback_summary, name="feedback_summary"),
    path("manage/events/new/", views.event_create, name="event_create"),
    path("registration/<int:reg_id>/mark-completed/", views.mark_completed, name="mark_completed"),
]

