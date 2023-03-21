from examples import custom_task_processor, custom_task_pvp, custom_task_metric
from script import Script
import json

def recursive_json_read(data, key: str):
    d = [data[k[1]] for k in enumerate(data) if key in k[1]]
    return d

with open("data.json", "r") as f:
    data = json.load(f)

file_name = data["file"]
model = data["model_para"]
if model == "gbert-base":
    model_type = "bert"
    model_name_or_path = "bert-base-cased"
else: # Clinical Bert
    '''Get Model Directory''' #TODO
    model_type = ""
    model_name_or_path = ""

task_name = [file_name.split(sep) for sep in ["_", ".", "-", "/"] if sep in file_name][0][0]

'''Configure Data Preprocessor'''
# define task name
custom_task_processor.MyTaskDataProcessor.TASK_NAME = task_name
# define labels
custom_task_processor.MyTaskDataProcessor.LABELS = recursive_json_read(data, "origin")

# define samples column
custom_task_processor.MyTaskDataProcessor.TEXT_A_COLUMN = int(data["sample"])
# define labels column
custom_task_processor.MyTaskDataProcessor.LABEL_COLUMN = int(data["label"])
# save entries as new task
custom_task_processor.report()  # save task

'''Configure Verbalizers'''
custom_task_pvp.MyTaskPVP.TASK_NAME = task_name
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
custom_task_metric.TASK_NAME = task_name
custom_task_metric.report()


'''Start training'''
instance = Script("pet", template_cnt, f"./data_uploaded/{file_name}", model_type,
                  model_name_or_path, task_name, "./output")  # set defined task names
instance.run()