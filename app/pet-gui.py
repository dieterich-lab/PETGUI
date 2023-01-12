import re
import time

from fastapi import FastAPI, File, Form, UploadFile, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import tarfile
import json
from Pet import script
from Pet.examples import custom_task_pvp, custom_task_processor
import re


app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")



loggings = {}
num = iter(range(20))
def write(i, html_content):
    """
    Write logging steps into html file "train.html"
    params:
        html_content = html skeleton content to write
        i = logging step to write
    """
    if i not in list(loggings.values()):
        with open("templates/train.html", "w") as f:
            if i == "Training done!":
                f.write(html_content.format(f"{i}"))
                loggings["final"] = i
            else:
                step = next(num)
                f.write(html_content.format(f"\tStep {step} in Training: {i}"))
                loggings[step] = i


def read(file):
    """
    Read training log: logging.txt and insert step 0
    params:
        file = logging.txt
    """
    with open(file, "r") as f:
        lines = f.readlines()
    lines.insert(0, "Training started\n")
    return lines

def iter_log(content):
    """
    Iterate over logging.txt and pass logging step to write()
    params:
        content = the html content to modify
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
            if "Saving complete" in log:
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
    write("Training done!", html_content)

@app.get("/logging", name="logging")
async def logging(request: Request, background_tasks: BackgroundTasks):
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
    background_tasks.add_task(iter_log, html_content)
    url = request.url_for("homepage")
    return templates.TemplateResponse("train.html", {"request": request, "log": "Training starting.."})


def read_logs(logs, lines):
    """
    Reads in current training process as lines (list) and returns new log line as str
    with updated log list containing line.
    Parameters:
         logs: list of processed log lines. [str(log), str(log),...]
         lines: list of logging.txt file
    Returns:
        l: current log
        logs, updated logs list
    """
    steps = {0: "Training started", 1:"Creating", 2:"Returning", 3:"Saving complete"}
    pattern = re.pattern = ".*(?=INFO)"  # strip date format
    try:
        for line in lines:
            match = re.findall(pattern, line)
            check = any([s for s in steps.values() if s in line])
            l = line.strip("".join(match))
            if check and l not in logs:
                logs.append(l)
                lines = lines[lines.index(line) + 1:]
                return l, logs, lines
            else:
                continue
    except:
        return "Waiting for step 1", logs, lines

@app.get("/")
def main():
    return {"Hello": "World"}


@app.get("/basic", response_class=HTMLResponse, name='homepage')
async def get_form(request: Request):
    with open("logging.txt", "w") as new_file:
        pass
    global loggings
    loggings = {}
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/progress", response_class=HTMLResponse, name="progress")
def read_item(request: Request):
    num = 100
    return templates.TemplateResponse("progress.html", {"request": request, "num": num})


def train(file):
    """
    Starts training with params and data_uploaded in Pet directory.
    """
    instance = script.Script("pet", [0], f"Pet/data_uploaded/{file}/", "bert", "bert-base-cased",
                      "yelp-task", "./output")  # set defined task names
    instance.run()

@app.get("/train", name="train")
async def kickoff(request: Request, background_tasks: BackgroundTasks):
    """
    Kicks off training by calling train method as background task with defined task name.
    """

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
    # define verbalizer for label 1
    custom_task_pvp.MyTaskPVP.VERBALIZER["1"].append(data["one"])
    # define verbalizer for label 2
    custom_task_pvp.MyTaskPVP.VERBALIZER["2"].append(data["two"])

    custom_task_pvp.MyTaskPVP.PATTERNS[0] = data["templates"]
    # save entries as new task
    custom_task_pvp.report() # save task

    '''Start Training'''
    file_name = data["file"]
    background_tasks.add_task(train, file_name)
    redirect_url = request.url_for('logging')
    return RedirectResponse(redirect_url, status_code=303)


@app.post("/basic")
async def get_form(request: Request,sample: str = Form(...), label: str = Form(...),templates: str = Form(...),one: str = Form(...), two: str = Form(...),model_para: str = Form(...),file: UploadFile = File(...)):
    file_upload = tarfile.open(fileobj=file.file, mode="r:gz")
    file_upload.extractall('./Pet/data_uploaded') # upload directly into Pet folder
    print(f'sample:{sample}')
    print(f'label:{label}')
    print(f'templates:{templates}')
    print(f'1:{one}')
    print(f'2:{two}')
    print(f'model_para:{model_para}')
    para_dic = {"file": file.filename.strip(".tar.gz"), "sample":sample,"label":label,"templates":templates,"one":one,"two":two,"model_para":model_para}
    with open('data.json', 'w') as f:
        json.dump(para_dic, f)
    redirect_url = request.url_for('train')
    return RedirectResponse(redirect_url, status_code=303)





    #return redirect(url_for('delete_images'))
    # redirect_url = request.url_for('basic_upload')
    # return RedirectResponse(redirect_url, status_code=303)

    # return {"filename": file.filename,"info":"upload successful"}

    #return templates.TemplateResponse("basic_upload.html", {"request": request})


# <input type='file' .... onchange='this.form.submit();'><br><br>

#
#
#
#
#
#
# from transformers import T5Tokenizer, T5ForConditionalGeneration
# @app.post("/translate_the_text")
# def translate_text(file: UploadFile = File(...)):
#     contents = file.file.read()
#     with open(file.filename,'wb') as f:
#         f.write(contents)
#     with open(file.filename) as file:
#         tras_data = file.read()
#     tokenizer = T5Tokenizer.from_pretrained('t5-small')
#     model = T5ForConditionalGeneration.from_pretrained('t5-small', return_dict=True)
#     input_ids = tokenizer("translate English to German: "+tras_data, return_tensors="pt").input_ids  # Batch size 1
#     outputs = model.generate(input_ids)
#     decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
#     with open("translated_text.txt","w") as q:
#         q.write(decoded)
#     file_location = "translated_text.txt"
#     return FileResponse(file_location, media_type='text/txt', filename="translated_text.txt")
   # # return {
   #          "input_text": tras_data,
   #          "translation_text": decoded
   #         }

# @app.get("/download-file")
# def download_file(upload_file):
#     file_path = upload_file.filename
#     return FileResponse(path=file_path, filename=file_path)

