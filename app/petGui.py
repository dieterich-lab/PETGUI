from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import tarfile
import json
from Pet import script
import os
from os.path import isdir, isfile
import pathlib
import shutil
from fastapi.encoders import jsonable_encoder
from config.celery_utils import create_celery
from celery_tasks.tasks import kickoff


def create_app() -> FastAPI:
    current_app = FastAPI(title="Asynchronous tasks processing with Celery and RabbitMQ",
                          description="Sample FastAPI Application to demonstrate Event "
                                      "driven architecture with Celery and RabbitMQ",
                          version="1.0.0", )

    current_app.celery_app = create_celery()
    return current_app


app = create_app()
celery = app.celery_app

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/logging/start_train")
async def get_run() -> dict:
    task = kickoff.apply_async()
    return JSONResponse({"task_id": task.id})



@app.get("/logging", name="logging")
async def logging(request: Request):
    return templates.TemplateResponse("next.html", {"request": request})


@app.get("/final", response_class=HTMLResponse, name='final')
async def get_final_template(request: Request):
    return templates.TemplateResponse("final_page.html", {"request": request})

@app.get("/")
def main():
    return {"Hello": "World"}

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
                    scores[k]["pre-rec-f1-supp"].append(f"Label: {l} Pre: {round(pre[l], 2)}, Rec: {round(rec[l], 2)},"
                                                        f"F1: {round(f1[l], 2)}, Supp: {supp[0]}")
                scores[k]["acc"] = acc
            scores[k]["pre-rec-f1-supp"] = [round(float(scr), 2) for l in scores.values() for scr in l]
        except:
            pass
    with open("results.json", "w") as res:
        json.dump(scores, res)

@app.get("/download", name="download")
def download():
    """
    Returns:
         final dict, e.g.: dict={p0-i0: {acc: 0.5, ...}, ...}
    """
    return FileResponse("results.json", filename="results.json")


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

@app.get("/log", name = "log")
async def read_log():
    global last_pos
    with open(log_file, "r") as file:
        file.seek(last_pos)
        lines = file.readlines()
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
    global last_pos
    last_pos = 0
    redirect_url = request.url_for('logging')
    print(para_dic)
    return RedirectResponse(redirect_url, status_code=303)
