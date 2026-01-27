from django.dispatch import receiver
from django.db.models.signals import post_save

from common.managers.cache.constants import CachedModel


@receiver(post_save)
def refresh_cache(sender, instance, created, **kwargs):
    if isinstance(instance, CachedModel.values_tuple()):
        sender.objects.refresh_cache()
