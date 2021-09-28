from __future__ import absolute_import, unicode_literals

from celery import shared_task
from celery.utils.log import get_task_logger
from .enums import TransactionType


@shared_task(bind=True, track_started=True)
def send_SMS(self, message):
    return message
