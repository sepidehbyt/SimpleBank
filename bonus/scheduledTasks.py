from __future__ import absolute_import, unicode_literals

from celery import shared_task
from celery.utils.log import get_task_logger


@shared_task(bind=True, track_started=True)
def c_get_tweets(self):
    return "Celery Loves Sepi"
