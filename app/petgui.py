import csv
import time
from fastapi import FastAPI, File, Form, UploadFile, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import tarfile
import json
from Pet import script
from Pet.examples import custom_task_pvp, custom_task_processor, custom_task_metric
import re
import os
from os.path import isdir, isfile
import pathlib
import shutil


app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", name="hello")
def main():
    return {"Hello": "World"}


def write(i, html_content, url=None):
    """
    Writes logging steps & final message into html file "run.html"
    params:
        html_content: str = html skeleton to write
        i: str = PET step to write
    """
    if i not in list(loggings.values()):
        with open("templates/run.html", "w") as f:
            if i == "PET done!":
                f.write(html_content.format(f"{i}<hr><a href={url}><button>See Results</button></a>"))
                loggings["final"] = i
            else:
                step = next(num)
                f.write(html_content.format(f"\tStep {step} in PET:<br/>{i}"))
                loggings[step] = i


@app.get("/results", name="results")
def results(request: Request):
    """
    Saves results.json for each pattern-iteration pair of output/final directory in a dictionary.
    Returns:
        html page with results & homepage redirection buttons
    """
    dirs = next(os.walk("output/final/"))[1]
    scores = {}
    for d in dirs:
        scores[d] = {"acc": int, "pre-rec-f1-supp": []}
        with open(f"output/final/{d}/results.json") as f:
            json_scores = json.load(f)
            acc = json_scores["test_set_after_training"]["acc"]
            pre, rec, f1, supp = json_scores["test_set_after_training"]["pre-rec-f1-supp"]
            scores[d]["acc"] = acc
            labels = [i for i in range(len(pre))]
            for l in labels:
                scores[d]["pre-rec-f1-supp"].append(f"Label: {l} pre: {pre[l]}, rec: {rec[l]}, f1: {f1[l]}, "
                                                    f"supp: {supp[0]}")
    with open("results.json", "w") as res:
        json.dump(scores, res)
    url_homepage, url_download = request.url_for("cleanup"), request.url_for("download")
    return templates.TemplateResponse("results.html", {"request": request, "scores": scores,
                                                       "url_homepage": url_homepage, "url_download": url_download})


@app.get("/download", name="download")
def download():
    """
    Returns:
         final dict, e.g.: dict={p0-i0: {acc: 0.5, ...}, ...}
    """
    return FileResponse("results.json", filename="results.json")

@app.get("/cleanup", name="cleanup")
def clean(request: Request=None):
    """
    Iterates over created paths during PET and unlinks them.
    Returns:
        redirection to homepage
    """
    paths = ["results.json", "data.json", "output", "Pet/data_uploaded"]
    for path in paths:
        file_path = pathlib.Path(path)
        if isfile(path):
            file_path.unlink()
        elif isdir(path):
            shutil.rmtree(path)
    if request:
        url = request.url_for("homepage")
        return RedirectResponse(url, status_code=303)
    else:
        return None

def read(file):
    """
    Reads PET log file: logging.txt and inserts step 0
    Params:
        file: str = logging.txt
    """
    with open(file, "r") as f:
        lines = f.readlines()
    lines.insert(0, "PET started\n")
    return lines


def iter_log(content, url=None):
    """
    Iterates over logging.txt continuously and passes logging step to function: write()
    Params:
        content: str = the html content to modify
        url: str = url link to "results"
    """
    st = round(time.time())
    logs = []
    lines = read("logging.txt")
    while st:
        try:
            time.sleep(10)
            log, logs, lines = read_logs(logs, lines)
            write(log, content)
            st = round(time.time())
            # Check if PET is done via full run-through or already existing outputs
            if "Saving complete" in log or "already exists" in log:
                st = False
        except:
            pass
    html_content = """
    <html>
        <body>
            {}
        </body>
    </html>
    """
    write("PET done!", html_content, url)


@app.get("/logging", name="logging")
async def logging(request: Request, background_tasks: BackgroundTasks):
    """
    Creates initial run.html and adds background task for iterating over logging.txt
    """
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
    write("{{log}}", html_content)
    url = request.url_for("results")
    background_tasks.add_task(iter_log, html_content, url)
    return templates.TemplateResponse("run.html", {"request": request, "log": "PET starting.."})




def read_logs(logs, lines):
    """
    Reads in current training process as lines (list) and returns new log line as str
    with updated log list containing line.
    Parameters:
         logs: list = processed log lines. [str(log), str(log),...]
         lines: list = logging.txt lines
    Returns:
        l: str = current log
        logs: list = updated logs
        lines: list = remaining (unprocessed) lines
    """
    pattern = re.pattern = ".*(?=INFO)"  # strip date format
    try:
        for line in lines:
            match = re.findall(pattern, line)
            check = any([s for s in id_to_steps.values() if re.findall(s, line)])
            l = line.strip("".join(match))
            if check and l not in logs:
                logs.append(l)
                lines = lines[lines.index(line) + 1:]
                return l, logs, lines
            else:
                continue
    except:
        return "Waiting for step 1", logs, lines



@app.get("/basic", response_class=HTMLResponse, name='homepage')
async def get_form(request: Request):
    """
    Creates empty file logging.txt and returns template for homepage
    """
    open("logging.txt", 'w').close()
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/progress", response_class=HTMLResponse, name="progress")
def read_item(request: Request):
    """
    Dummy progress bar
    """
    max = 100
    return templates.TemplateResponse("progress.html", {"request": request, "num": max})


def pet(task_name, file_name):
    """
    Starts PET with params and data_uploaded in Pet directory.
    Params:
        file: str = filename of dataset
    """
    instance = script.Script("pet", [0], f"Pet/data_uploaded/{file_name}/", "bert", "bert-base-cased",
                      f"{task_name}", "./output")  # set defined task names
    try:
        instance.run()
    except:
        print("###FAILED###")
        convey(False)
        raise Exception


def convey(started: bool):
    global Pet_started
    Pet_started = started

@app.get("/run", name="run")
async def kickoff(request: Request, background_tasks: BackgroundTasks):
    """
    TODO: Require user specification of task name
    Kicks off PET by calling pet() as background task with defined task & file name.
    Sets custom parameters for pvp, data processing and evaluation metrics.
    Redirects to "logging"
    """
    global loggings, num, id_to_steps, steps_to_id, Pet_started
    loggings = {}
    num = iter(range(10))
    Pet_started = True

    id_to_steps = {0: "Training started", 1: "Creating", 2: "Returning", 3: "Saving complete",
                   4: r"/final/p\d+-i\d+ already exists"}
    steps_to_id = {v: k for k, v in id_to_steps.items()}

    with open("data.json", "r") as f:
        data = json.load(f)

    '''Configure Data Preprocessor'''
    # define task name
    task_name = "yelp-task"
    custom_task_processor.MyTaskDataProcessor.TASK_NAME = task_name
    # define labels
    file_name = data["file"]
    custom_task_processor.MyTaskDataProcessor.LABELS = ["1", "2"]
    # define samples column
    custom_task_processor.MyTaskDataProcessor.TEXT_A_COLUMN = int(data["sample"])
    # define labels column
    custom_task_processor.MyTaskDataProcessor.LABEL_COLUMN = int(data["label"])
    # save entries as new task
    custom_task_processor.report()

    '''Configure Verbalizers'''
    custom_task_pvp.MyTaskPVP.TASK_NAME = task_name
    # define verbalizer for label 1
    custom_task_pvp.MyTaskPVP.VERBALIZER["1"].append(data["one"])
    # define verbalizer for label 2
    custom_task_pvp.MyTaskPVP.VERBALIZER["2"].append(data["two"])

    custom_task_pvp.MyTaskPVP.PATTERNS[0] = data["templates"]
    # save entries as new task
    custom_task_pvp.report()

    '''Configure Metrics'''
    custom_task_metric.TASK_NAME = task_name
    custom_task_metric.report()

    '''Start PET'''
    background_tasks.add_task(pet, task_name, file_name)
    time.sleep(3)
    if Pet_started:
        redirect_url = request.url_for('logging')
        return RedirectResponse(redirect_url, status_code=303)
    else:
        print(Pet_started)
        return {"PET": "FAILED"}



def get_labels(filename, lab_col: int, delimiter: str):
    """
    TODO: Fix reader (throws error on logits when used here) & require delimiter specification
    Returns set of labels from train.csv of provided file
    Params:
        filename: str = the filename to return labels for
        lab_col: int = the column number of the labels in train.csv
        delimiter: str = the delimiter by which the columns are separated
    Returns:
        a set of the labels
    """
    labels = []

    with open(f"Pet/data_uploaded/{filename}/train.csv") as f:
        lines = f.readlines()
        for line in lines:
            line = line.split(delimiter)
            lab = int(line[lab_col])
            labels.append(lab)
    return set(labels)

@app.post("/basic")
async def get_form(request: Request, sample: str = Form(...), label: str = Form(...), templates: str = Form(...),
                   one: str = Form(...), two: str = Form(...), model_para: str = Form(...),
                   file: UploadFile = File(...)):
    """TODO: Read in gbert
    Reads in user specified parameters for PET.
    Redirects to "train" for start of training
    """
    file_upload = tarfile.open(fileobj=file.file, mode="r:gz")
    file_upload.extractall('./Pet/data_uploaded')
    print(f'sample:{sample}')
    print(f'label:{label}')
    print(f'templates:{templates}')
    print(f'1:{one}')
    print(f'2:{two}')
    print(f'model_para:{model_para}')
    para_dic = {"file": file.filename.strip(".tar.gz"), "sample": sample, "label": label, "templates": templates,
                "one": one, "two": two, "model_para": model_para}
    with open('data.json', 'w') as f:
        json.dump(para_dic, f)
    redirect_url = request.url_for('run')
    return RedirectResponse(redirect_url, status_code=303)
