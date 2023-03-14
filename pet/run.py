from examples import custom_task_processor, custom_task_pvp, custom_task_metric
from script import Script
import json

def recursive_json_read(data, key: str):
    d = []
    for i in range(5):
        if f"{key}_{i}" in data:
            d.append(data[f"{key}_{i}"])
    return d

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

'''Start training'''
instance = Script("pet", template_cnt, "./data_uploaded/yelp_review_polarity_csv", "bert", "bert-base-cased",
                         "yelp-task", "./output")  # set defined task names
instance.run()