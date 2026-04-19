from __future__ import annotations

import hashlib

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from io import BytesIO

from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import User

from .forms import EventForm, FeedbackForm, RegistrationForm
from .models import Attendance, Event, Feedback, Registration
from .utils import build_certificate_pdf


def home(request: HttpRequest) -> HttpResponse:
    upcoming = Event.objects.filter(is_published=True).order_by("start_at")[:6]
    return render(request, "events/home.html", {"upcoming": upcoming})


def event_list(request: HttpRequest) -> HttpResponse:
    category = request.GET.get("category", "all")
    query = request.GET.get("q", "").strip()

    events = Event.objects.filter(is_published=True)
    if category in {Event.Category.TECH, Event.Category.NON_TECH}:
        events = events.filter(category=category)

    if query:
        events = events.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(venue__icontains=query))

    events = events.order_by("start_at")
    return render(request, "events/event_list.html", {"events": events, "category": category, "query": query})


def event_detail(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, id=event_id, is_published=True)
    reg = None
    attended = False
    left_feedback = False
    if request.user.is_authenticated:
        reg = Registration.objects.filter(event=event, student=request.user, status__in=[Registration.Status.PENDING, Registration.Status.COMPLETED]).first()
        attended = Attendance.objects.filter(event=event, student=request.user).exists()
        left_feedback = Feedback.objects.filter(event=event, student=request.user).exists()
    return render(
        request,
        "events/event_detail.html",
        {"event": event, "registration": reg, "attended": attended, "left_feedback": left_feedback},
    )


def _build_certificate_id(reg_id: int) -> str:
    return f"CERT-2026-{reg_id:04d}"


@role_required(User.Role.STUDENT)
def certificate_preview(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, id=event_id, is_published=True)
    reg = Registration.objects.filter(event=event, student=request.user, status=Registration.Status.COMPLETED).first()
    if not reg:
        messages.error(request, "Certificate preview is available only after admin marks the event as completed.")
        return redirect("events:event_detail", event_id=event.id)

    organizer_name = None
    if event.organizer_id:
        organizer = User.objects.filter(id=event.organizer_id).first()
        if organizer:
            organizer_name = organizer.get_full_name() or organizer.username

    certificate_id = _build_certificate_id(reg.id)
    return render(
        request,
        "events/certificate_preview.html",
        {
            "event": event,
            "student_name": request.user.get_full_name() or request.user.username,
            "organizer_name": organizer_name,
            "certificate_id": certificate_id,
            "current_date": timezone.localtime(timezone.now()).strftime("%d %b %Y"),
        },
    )


@role_required(User.Role.STUDENT)
def certificate_list(request: HttpRequest) -> HttpResponse:
    registrations = Registration.objects.filter(student=request.user).select_related("event").order_by("-created_at")
    return render(request, "certificate.html", {"registrations": registrations})


def verify_certificate(request: HttpRequest, certificate_id: str) -> HttpResponse:
    try:
        # Extract reg_id from CERT-2026-XXXX
        if not certificate_id.startswith("CERT-2026-"):
            raise ValueError
        reg_id = int(certificate_id[10:])
        reg = Registration.objects.select_related("event", "student").get(id=reg_id, status=Registration.Status.COMPLETED)
        organizer_name = None
        if reg.event.organizer_id:
            organizer = User.objects.filter(id=reg.event.organizer_id).first()
            if organizer:
                organizer_name = organizer.get_full_name() or organizer.username
        return render(request, "events/verify_certificate.html", {
            "reg": reg,
            "student_name": reg.student.get_full_name() or reg.student.username,
            "organizer_name": organizer_name,
            "certificate_id": certificate_id,
            "current_date": timezone.localtime(timezone.now()).strftime("%d %b %Y"),
        })
    except (ValueError, Registration.DoesNotExist):
        return render(request, "events/verify_certificate.html", {"invalid": True})


def admin_login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated and request.user.role == User.Role.ADMIN:
        return redirect("custom_admin_dashboard")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password", "").strip()
        if username == "hemath":
            user, created = User.objects.get_or_create(
                username="hemath",
                defaults={"email": "hemath@example.com", "role": User.Role.ADMIN},
            )
            if created or not user.check_password("hem@552004"):
                user.set_password("hem@552004")
                user.save()
            if user.check_password(password):
                if user.role != User.Role.ADMIN:
                    user.role = User.Role.ADMIN
                    user.save(update_fields=["role"])
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                return redirect("custom_admin_dashboard")
            else:
                error = "Invalid credentials"
        else:
            error = "Invalid credentials"

    return render(request, "events/admin_login.html", {"error": error})


@role_required(User.Role.ADMIN, User.Role.ORGANIZER)
def event_create(request: HttpRequest) -> HttpResponse:
    form = EventForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        event: Event = form.save(commit=False)
        event.created_by = request.user  # type: ignore[assignment]
        if request.user.role == User.Role.ORGANIZER:
            event.organizer = request.user  # type: ignore[assignment]
        event.save()
        messages.success(request, "Event created.")
        return redirect("events:event_detail", event_id=event.id)
    return render(request, "events/event_form.html", {"form": form, "title": "Create event"})


@role_required(User.Role.ADMIN, User.Role.ORGANIZER)
def event_edit(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, id=event_id)
    if request.user.role == User.Role.ORGANIZER and event.organizer_id != request.user.id:
        messages.error(request, "You can only edit your own events.")
        return redirect("events:organizer_events")

    form = EventForm(request.POST or None, request.FILES or None, instance=event)
    if request.user.role == User.Role.ORGANIZER:
        form.fields["organizer"].disabled = True
        form.fields["is_published"].disabled = False

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Event updated.")
        return redirect("events:event_detail", event_id=event.id)
    return render(request, "events/event_form.html", {"form": form, "title": "Edit event"})


@role_required(User.Role.STUDENT)
def register_for_event(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, id=event_id, is_published=True)
    if not event.is_registration_open():
        messages.error(request, "Registration is closed for this event.")
        return redirect("events:event_detail", event_id=event.id)

    if event.seats_left() <= 0:
        messages.error(request, "Event is full.")
        return redirect("events:event_detail", event_id=event.id)

    existing = Registration.objects.filter(event=event, student=request.user).first()
    if existing:
        messages.info(request, "You have already registered for this event.")
        return redirect("events:my_registrations")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        Registration.objects.create(
            event=event,
            student=request.user,  # type: ignore[arg-type]
            name=form.cleaned_data["name"],
            phone=form.cleaned_data["phone"],
            year=form.cleaned_data["year"],
            department=form.cleaned_data["department"],
        )
        messages.success(request, "Registered successfully.")
        return redirect("events:my_registrations")

    return render(request, "events/register.html", {"event": event, "form": form})


@role_required(User.Role.STUDENT)
def my_registrations(request: HttpRequest) -> HttpResponse:
    regs = Registration.objects.filter(student=request.user, status__in=[Registration.Status.PENDING, Registration.Status.COMPLETED]).select_related("event")
    return render(request, "events/my_registrations.html", {"registrations": regs})


@role_required(User.Role.ORGANIZER, User.Role.ADMIN)
def organizer_events(request: HttpRequest) -> HttpResponse:
    if request.user.role == User.Role.ADMIN:
        events = Event.objects.all().order_by("-start_at")
    else:
        events = Event.objects.filter(organizer=request.user).order_by("-start_at")
    return render(request, "events/organizer_events.html", {"events": events})

@role_required(User.Role.ADMIN)
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    event_filter = request.GET.get("event", "")
    user_filter = request.GET.get("user", "")
    search = request.GET.get("q", "").strip()

    registrations = Registration.objects.select_related("event", "student").all()
    if event_filter:
        registrations = registrations.filter(event__title__icontains=event_filter)
    if user_filter:
        registrations = registrations.filter(student__username__icontains=user_filter)
    if search:
        registrations = registrations.filter(
            Q(student__username__icontains=search)
            | Q(student__email__icontains=search)
            | Q(event__title__icontains=search)
            | Q(phone__icontains=search)
        )

    registrations = registrations.order_by("-created_at")
    stats = {
        "events": Event.objects.count(),
        "registrations": registrations.count(),
        "students": User.objects.filter(role=User.Role.STUDENT).count(),
        "organizers": User.objects.filter(role=User.Role.ORGANIZER).count(),
    }
    return render(
        request,
        "events/admin_dashboard.html",
        {
            "registrations": registrations,
            "stats": stats,
            "event_filter": event_filter,
            "user_filter": user_filter,
            "search": search,
        },
    )


@role_required(User.Role.ORGANIZER, User.Role.ADMIN)
def attendance_mark(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, id=event_id)
    if request.user.role == User.Role.ORGANIZER and event.organizer_id != request.user.id:
        raise Http404()

    regs = (
        Registration.objects.filter(event=event, status=Registration.Status.PENDING)
        .select_related("student")
        .order_by("student__username")
    )
    already = set(Attendance.objects.filter(event=event).values_list("student_id", flat=True))

    if request.method == "POST":
        selected_ids = {int(x) for x in request.POST.getlist("present") if str(x).isdigit()}
        to_create = [Attendance(event=event, student_id=sid, marked_by=request.user) for sid in selected_ids if sid not in already]
        Attendance.objects.bulk_create(to_create, ignore_conflicts=True)
        messages.success(request, "Attendance saved.")
        return redirect("events:attendance", event_id=event.id)

    return render(request, "events/attendance.html", {"event": event, "registrations": regs, "already": already})


@role_required(User.Role.ADMIN)
def mark_completed(request: HttpRequest, reg_id: int) -> HttpResponse:
    if request.method != "POST":
        raise Http404()
    reg = get_object_or_404(Registration, id=reg_id, status=Registration.Status.PENDING)
    reg.status = Registration.Status.COMPLETED
    reg.save()
    messages.success(request, f"Marked {reg.student.username} as completed for {reg.event.title}.")
    return redirect("events:admin_dashboard")


@role_required(User.Role.STUDENT)
def download_certificate(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, id=event_id, is_published=True)
    reg = Registration.objects.filter(event=event, student=request.user, status=Registration.Status.COMPLETED).first()
    if not reg:
        messages.error(request, "Certificate is available only after admin marks the event as completed.")
        return redirect("events:event_detail", event_id=event.id)

    organizer_name = None
    if event.organizer_id:
        organizer = User.objects.filter(id=event.organizer_id).first()
        if organizer:
            organizer_name = organizer.get_full_name() or organizer.username

    certificate_id = _build_certificate_id(reg.id)
    pdf_bytes = build_certificate_pdf(
        student=request.user,
        event=event,
        organizer_name=organizer_name,
        certificate_id=certificate_id,
    )
    filename = f"certificate_{certificate_id}.pdf"
    return FileResponse(
        BytesIO(pdf_bytes),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )


@role_required(User.Role.STUDENT)
def leave_feedback(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, id=event_id, is_published=True)
    # Feedback after event
    if timezone.now() < event.start_at:
        messages.error(request, "Feedback opens after the event.")
        return redirect("events:event_detail", event_id=event.id)

    attended = Attendance.objects.filter(event=event, student=request.user).exists()
    if not attended:
        messages.error(request, "Only attendees can leave feedback.")
        return redirect("events:event_detail", event_id=event.id)

    feedback = Feedback.objects.filter(event=event, student=request.user).first()
    form = FeedbackForm(request.POST or None, instance=feedback)
    if request.method == "POST" and form.is_valid():
        fb = form.save(commit=False)
        fb.event = event
        fb.student = request.user  # type: ignore[assignment]
        fb.save()
        messages.success(request, "Thanks for your feedback!")
        return redirect("events:event_detail", event_id=event.id)
    return render(request, "events/feedback.html", {"event": event, "form": form})


@role_required(User.Role.ORGANIZER, User.Role.ADMIN)
def feedback_summary(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, id=event_id)
    if request.user.role == User.Role.ORGANIZER and event.organizer_id != request.user.id:
        raise Http404()

    stats = event.feedback.aggregate(avg=Avg("rating"), count=Count("id"))
    feedback = event.feedback.select_related("student").order_by("-created_at")
    return render(request, "events/feedback_summary.html", {"event": event, "stats": stats, "feedback": feedback})
