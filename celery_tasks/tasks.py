from celery import shared_task
from Pet.examples import custom_task_pvp, custom_task_processor, custom_task_metric
import json
import threading


@shared_task(bind=False, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5},
             name='training:kickoff')
def kickoff():
    """
    Kicks off PET by calling train method as background task with defined task name.
    """
    from app.petGui import train, recursive_json_read

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
    custom_task_processor.report() # save task

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
    custom_task_pvp.report() # save task

    '''Configure Metrics'''
    custom_task_metric.TASK_NAME = "yelp-task"
    custom_task_metric.report()

    '''Start PET'''
    file_name = data["file"]
    #t = threading.Thread(target=train, args=(file_name, template_cnt))
    #t.start()
    train(file_name,template_cnt)
