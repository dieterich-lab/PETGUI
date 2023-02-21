from typing import List

from celery import shared_task

import universities


uni = universities.API()


@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5},
             name='university:get_university_task')
def get_university_task(country):
        data : dict = {}
        data[country] = list(uni.search(country))
        return country
