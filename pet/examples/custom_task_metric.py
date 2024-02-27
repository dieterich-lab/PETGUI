from pet.tasks import METRICS

TASK_NAME = None

def report():
    METRICS[TASK_NAME] = ["acc", "pre-rec-f1-supp"]
