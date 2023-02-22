from typing import List
from celery import shared_task
import universities
from Pet.examples import custom_task_pvp, custom_task_processor, custom_task_metric
from fastapi import Request
from fastapi.responses import RedirectResponse
import json

uni = universities.API()


@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5},
             name='university:get_university_task')
def get_university_task(self, cnt: str):
        data : dict = {}
        data[cnt] = list(uni.search(country = cnt))
        return data

@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5},
             name='training:get_run_task')
def get_run_task(self):
    from app.petGui import recursive_json_read, train

    with open("data.json", "r") as f:
        data = json.load(f)

    '''Configure Data Preprocessor'''
    # define task name
    custom_task_processor.MyTaskDataProcessor.TASK_NAME = "yelp-task"
    # define labels
    custom_task_processor.MyTaskDataProcessor.LABELS = ["1", "2"]
    # define samples column
    custom_task_processor.MyTaskDataProcessor.TEXT_A_COLUMN = int(data["sample"])
    # define labels column
    custom_task_processor.MyTaskDataProcessor.LABEL_COLUMN = int(data["label"])
    # save entries as new task
    custom_task_processor.report()  # save task

    '''Configure Verbalizers'''
    custom_task_pvp.MyTaskPVP.TASK_NAME = "yelp-task"
    # define label-verbalizer mappings
    labels = recursive_json_read(data, "origin")
    verbalizers = recursive_json_read(data, "mapping")
    for l, v in zip(labels, verbalizers):
        custom_task_pvp.MyTaskPVP.VERBALIZER[l] = [v]
    templates = recursive_json_read(data, "template")
    template_cnt = list(range(len(templates)))
    for i in template_cnt:
        custom_task_pvp.MyTaskPVP.PATTERNS[i] = templates[i]
    # save entries as new task
    custom_task_pvp.report()  # save task

    '''Configure Metrics'''
    custom_task_metric.TASK_NAME = "yelp-task"
    custom_task_metric.report()

    '''Start PET'''
    file_name = data["file"]
    train(file_name, template_cnt)
    #redirect_url = request.url_for('logging')
    #return RedirectResponse(redirect_url, status_code=303)


@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5},
             name='logging:get_logging_task')
def get_logging_task(self, url, loggings, num):
    from app.petGui import iter_log, write
    html_content = """
    <html>
        <head>
            <meta http-equiv="refresh" content="3">
        </head>
        <body>
            {}
        </body>
    </html>
    """
    write("{{log}}", html_content, loggings = loggings, num = num)
    iter_log(html_content, url)

