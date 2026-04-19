from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import OrganizerProfile, User


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profiles(sender, instance: User, created: bool, **kwargs):
    if instance.role == User.Role.ORGANIZER:
        OrganizerProfile.objects.get_or_create(user=instance)
