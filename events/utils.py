from __future__ import annotations

from io import BytesIO

from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from accounts.models import User

from .models import Event


def build_certificate_pdf(*, student: User, event: Event, organizer_name: str | None = None, certificate_id: str | None = None) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Background / border
    margin = 1.2 * cm
    c.setLineWidth(2)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    if certificate_id:
        c.setFont("Helvetica", 9)
        c.drawRightString(width - 2.3 * cm, height - 2.3 * cm, certificate_id)

    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 4 * cm, "Certificate of Participation")

    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 5.3 * cm, "This is to certify that")

    c.setFont("Helvetica-Bold", 22)
    name = (student.get_full_name() or student.username).strip()
    c.drawCentredString(width / 2, height - 7.2 * cm, name)

    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 8.5 * cm, "has successfully participated in")

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 10 * cm, event.title)

    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 11.5 * cm, f"Venue: {event.venue}")
    c.drawCentredString(width / 2, height - 12.2 * cm, f"Date: {timezone.localtime(event.start_at).strftime('%d %b %Y, %I:%M %p')}")

    c.setFont("Helvetica", 10)
    c.drawString(2.2 * cm, 2.6 * cm, f"Issued on: {timezone.localtime(timezone.now()).strftime('%d %b %Y')}")

    if certificate_id:
        c.setFont("Helvetica", 9)
        c.drawString(2.2 * cm, 2.0 * cm, f"Verify at: https://yourdomain.com/certificate/verify/{certificate_id}")

    if organizer_name:
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 2.2 * cm, 3.2 * cm, "Organizer")
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(width - 2.2 * cm, 2.6 * cm, organizer_name)

    c.showPage()
    c.save()
    return buffer.getvalue()

