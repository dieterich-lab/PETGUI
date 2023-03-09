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
import threading
import os
from os.path import isdir, isfile
import pathlib
import shutil
from fastapi.encoders import jsonable_encoder
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pandas as pd



app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# def write(cont, html_content, url=None):
#     """
#     Write logging steps into html file "run.html"
#     params:
#         html_content = html skeleton content to write
#         cont: str/list = logging content (either list or str) to write
#     """
#     if isinstance(cont, list):
#         if any([c not in list(loggings.values()) for c in cont]):
#             with open("templates/run.html", "w") as f:
#                 texts = []
#                 for t in cont:
#                     if t in loggings.values():
#                         step = [str(k) for k in loggings.keys() if loggings[k] == t]
#                         step = int("".join(step))
#                     else:
#                         step = next(num)
#                     texts.append(f"<b>Step {step} in PET:</b><br/> {t}<br/>")
#                     loggings[step] = t
#                 if "PET done!" in cont:
#                     texts.append(f"<hr><a href={url}><button>See Results</button></a>")
#                 f.write(html_content.format("".join(texts)))
#     else:
#         if cont not in list(loggings.values()):
#             with open("templates/run.html", "w") as f:
#                 step = next(num)
#                 f.write(html_content.format(f"<b>Step {step} in PET:</b><br/> {cont}<br/>"))
#             loggings[step] = cont

# def read(file):
#     """
#     Read PET log: logging.txt and insert step 0
#     params:
#         file = logging.txt
#     """
#     with open(file, "r") as f:
#         lines = f.readlines()
#     lines.insert(0, "PET started\n")
#     return lines


# def iter_log(content, url=None):
#     """
#     Iterate over logging.txt and pass logging step to write()
#     params:
#         content = the html content to modify
#     """
#     st = round(time.time())
#     logs, cont = [], []
#     lines = read("logging.txt")
#     html_content = """
#     <html>
#         <body>
#             {}
#         </body>
#     </html>
#     """
#     while st:
#         time.sleep(7)
#         try:
#             log, logs, lines = read_logs(logs, lines)
#             if "final" in log:
#                 log = "PET done!"
#             cont.append(log)
#             if len(cont) == 3:
#                 if log == "PET done!":
#                     write(cont, html_content, url)
#                     cont.pop(0)
#                     st = False
#                 else:
#                     write(cont, content)
#                     cont.pop(0)
#         except TypeError:
#             pass
#     write(cont, html_content, url)


# @app.get("/logging", name="logging")
# async def logging(request: Request, background_tasks: BackgroundTasks):
#     html_content = """
#     <html>
#         <head>
#             <meta http-equiv="refresh" content="3">
#         </head>
#         <body>
#             {}
#         </body>
#     </html>
#     """
#     write("{{log}}", html_content)
#     url = request.url_for("results")
#     background_tasks.add_task(iter_log, html_content, url)
#     return templates.TemplateResponse("run.html", {"request": request, "log": "PET starting.."})


# def read_logs(logs, lines):
#     """
#     Reads in current PET progress as lines (list) and returns new log line as str
#     with updated log list containing line.
#     Parameters:
#          logs: list of processed log lines. [str(log), str(log),...]
#          lines: list of logging.txt file
#     Returns:
#         l: current log
#         logs, updated logs list
#     """
#     steps = {0: "PET started", 1: "Creating", 2: "Returning", 3: "Saving trained", 4: "Starting", 5: "Skipping subdir"}
#     pattern = re.pattern = ".*(?=INFO|WARNING)"  # strip date format
#     try:
#         for line in lines:
#             match = re.findall(pattern, line)
#             check = any([s for s in steps.values() if s in line])
#             l = line.strip("".join(match))
#             if check and line not in logs:
#                 logs.append(line)
#                 lines = lines[lines.index(line):]
#                 return l, logs, lines
#             else:
#                 continue
#     except IndexError:
#         return "Waiting for step 1", logs, lines

# @app.get("/log")
# async def read_log():
#     global last_pos
#     with open(log_file, "r") as file:
#         file.seek(last_pos)
#         lines = file.readlines()
#         last_pos = file.tell()
#
#     info_lines = [line for line in lines if "INFO" in line and "WARNING" not in line]
#     return {"log": info_lines}


@app.get("/logging", name="logging")
async def logging(request: Request):
    return templates.TemplateResponse("next.html", {"request": request})



@app.get("/final", response_class=HTMLResponse, name='final')
async def get_final_template(request: Request):
    return templates.TemplateResponse("final_page.html", {"request": request})

@app.get("/")
def main():
    return RedirectResponse(url="/basic")
    #return {"Hello": "World"}

#@app.get("/results", name="results")
def results():
    """
    Saves results.json for each pattern-iteration pair of output/final directory in a dictionary.
    Returns:
        html page with results & homepage redirection buttons
    """
    dirs = next(os.walk("output/"))[1]
    scores = {}
    for i, d in enumerate(dirs, 1):
        final = ""
        if "final" in d:
            k = "Final"
            scores[k] = {"acc": "-", "pre-rec-f1-supp": []}
            finals = next(os.walk("output/final/"))[1]
            assert len(finals) == 1
            final += f"/{finals[0]}"
        else:
            k = f"Pattern-{i} Iteration 1"
            scores[k] = {"acc": "-", "pre-rec-f1-supp": []}
            final = ""
        try:
            with open(f"output/{d}{final}/results.json") as f:
                json_scores = json.load(f)
                acc = round(json_scores["test_set_after_training"]["acc"], 2)
                pre, rec, f1, supp = json_scores["test_set_after_training"]["pre-rec-f1-supp"]
                labels = [i for i in range(len(pre))]
                for l in labels:
                    scores[k]["pre-rec-f1-supp"].append(f"Label: {l} pre: {pre[l]}, rec: {rec[l]}, f1: {f1[l]}, "
                                                        f"supp: {supp[0]}")
                scores[k]["acc"] = acc
        except:
            pass
    with open("results.json", "w") as res:
        json.dump(scores, res)
    #url_homepage, url_download = request.url_for("cleanup"), request.url_for("download")
    # return templates.TemplateResponse("results.html", {"request": request, "scores": scores,
    #                                                    "url_homepage": url_homepage, "url_download": url_download})


@app.get("/download", name="download")
def download():
    """
    Returns:
         final dict, e.g.: dict={p0-i0: {acc: 0.5, ...}, ...}
    """
    return FileResponse("results.json", filename="results.json")

@app.get("/download_prediction", name="download_prediction")
def download_predict():
    return FileResponse("predictions.csv", filename="predictions.csv")




@app.get("/cleanup")
def clean(request: Request):
    """
    Iterates over created paths during PET and unlinks them.
    Returns:
        redirection to homepage
    """
    paths = ["results.json", "data.json", "output", "Pet/data_uploaded", "templates/run.html","last_pos.txt"]
    for path in paths:
        file_path = pathlib.Path(path)
        if isfile(path):
            file_path.unlink()
        elif isdir(path):
            shutil.rmtree(path)
    url = request.url_for("homepage")
    # if request:
    return RedirectResponse(url, status_code=303)
    # else:
    #     return None


@app.get("/basic", response_class=HTMLResponse, name='homepage')
async def get_form(request: Request):
    with open("logging.txt", "w") as new_file:
        pass
    # global loggings, num
    # loggings = {}
    # num = iter(range(20))
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/progress", response_class=HTMLResponse, name="progress")
def read_item(request: Request):
    max_num = 100
    return templates.TemplateResponse("progress.html", {"request": request, "max_num": max_num})


def train(file, templates):
    """
    Starts training+testing with params and data_uploaded in Pet directory.
    """
    instance = script.Script("pet", templates, f"Pet/data_uploaded/{file}/", "bert", "bert-base-cased",
                             "yelp-task", "./output")  # set defined task names
    instance.run()

    with open('logging.txt', 'a') as file:
        file.write('Training Complete\n')
    # Call results()
    results()


@app.get("/logging/start_train")
async def kickoff(request: Request):
    """
    Kicks off PET by calling train method as background task with defined task name.
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
    t = threading.Thread(target=train, args=(file_name, template_cnt))
    t.start()
    #train(file=file_name, templates=template_cnt)
    # Write to logging.txt


    # background_tasks.add_task(train, file_name, template_cnt)
    # redirect_url = request.url_for('logging')
    # return RedirectResponse(redirect_url, status_code=303)


def recursive_json_read(data, key: str):
    d = []
    for i in range(5):
        if f"{key}_{i}" in data:
            d.append(data[f"{key}_{i}"])
    return d

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    """
    Upload function for the final page
    """

    upload_folder = "./Pet/data_uploaded/unlabeled"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file.filename)
    with open(file_path, "wb") as file_object:
        file_object.write(file.file.read())
    return {"filename": file.filename, "path": file_path}


log_file = "logging.txt"
last_pos_file = "last_pos.txt"

# Initialize last_pos to the value stored in last_pos.txt, or 0 if the file does not exist
if os.path.exists(last_pos_file):
    with open(last_pos_file, "r") as file:
        last_pos = int(file.read())
else:
    last_pos = 0

@app.get("/log")
async def read_log():
    global last_pos
    with open(log_file, "r") as file:
        file.seek(last_pos)
        lines = file.readlines()
        print(lines)
        last_pos = file.tell()
    with open(last_pos_file, "w") as file:
        file.write(str(last_pos))
    info_lines = [line.strip() for line in lines if any(
        word in line for word in ["Creating", "Returning", "Saving", "Starting evaluation", "Training Complete"])]
    #redis_conn.set("last_pos", last_pos)  # update last_pos in Redis
    return {"log": info_lines}


@app.post("/basic", name="homepage")
async def get_form(request: Request, sample: str = Form(media_type="multipart/form-data"),
                   label: str = Form(media_type="multipart/form-data"),
                   origin_0: str = Form(media_type="multipart/form-data"),
                   mapping_0: str = Form(media_type="multipart/form-data"),
                   origin_1: str = Form(media_type="multipart/form-data"),
                   mapping_1: str = Form(media_type="multipart/form-data"),
                   model_para: str = Form(media_type="multipart/form-data"),
                   file: UploadFile = File(...),
                   template_0: str = Form(media_type="multipart/form-data")):

    file_upload = tarfile.open(fileobj=file.file, mode="r:gz")
    file_upload.extractall('./Pet/data_uploaded')
    da = await request.form()
    da = jsonable_encoder(da)
    #template_0 = da["template_0"]
    template_counter = 1
    origin_counter = 1
    mapping_counter = 1
    para_dic = {"file": file.filename.strip(".tar.gz"), "sample": sample, "label": label,
                "template_0": template_0, "origin_0": origin_0,
                "mapping_0": mapping_0,  "origin_1": origin_1,
                "mapping_1": mapping_1, "model_para": model_para}
    while f"template_{str(template_counter)}" in da: # Template
        template_key = f"template_{str(template_counter)}"
        para_dic[template_key] = da[template_key]
        template_counter = template_counter + 1
    while f"origin_{str(origin_counter)}" in da: # Label
        origin_key = f"origin_{str(origin_counter)}"
        para_dic[origin_key] = da[origin_key]
        origin_counter = origin_counter+1
    while f"mapping_{str(mapping_counter)}" in da: # Verbalizer
        mapping_key = f"mapping_{str(mapping_counter)}"
        para_dic[mapping_key] = da[mapping_key]
        mapping_counter = mapping_counter+1
    with open('data.json', 'w') as f:
        json.dump(para_dic, f)
    with open("logging.txt","w") as r:
        pass
    global last_pos
    last_pos = 0
    redirect_url = request.url_for('logging')
    print(para_dic)
    return RedirectResponse(redirect_url, status_code=303)



@app.get("/final/start_prediction")
async def label_prediction(request: Request):
    df = pd.read_csv("Pet/data_uploaded/yelp_review_polarity_csv/unlabeled.csv", header=None, names=['label', 'text'])
    tokenizer = BertTokenizer.from_pretrained('output/final/p0-i0')
    model = BertForSequenceClassification.from_pretrained('output/final/p0-i0')
    input_ids = []
    attention_masks = []
    for text in df['text']:
        encoded_dict = tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=64,
            pad_to_max_length=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        input_ids.append(encoded_dict['input_ids'])
        attention_masks.append(encoded_dict['attention_mask'])
    input_ids = torch.cat(input_ids, dim=0)
    attention_masks = torch.cat(attention_masks, dim=0)
    labels = torch.tensor(df['label'].values)
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_masks)
    logits = outputs[0]
    predictions = torch.argmax(logits, dim=1)
    df['label'] = predictions
    df.to_csv('predictions.csv', index=False)


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

