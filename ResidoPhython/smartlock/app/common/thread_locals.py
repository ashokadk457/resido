from threading import local

from django.dispatch import receiver
from django.core.signals import request_finished


_thread_locals = local()


def set_current_user(user):
    _thread_locals.user = user


def get_current_user():
    return getattr(_thread_locals, "user", None)


@receiver(request_finished)
def clear_current_user(sender, **kwargs):
    _thread_locals.user = None


def get_request():
    return getattr(_thread_locals, "request", None)
