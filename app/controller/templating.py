import threading
import uuid

from fastapi import Request, Depends, APIRouter, Form, File, UploadFile, Response, HTTPException, FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.responses import FileResponse
from fastapi.encoders import jsonable_encoder
import json, os, tarfile, subprocess
from subprocess import PIPE
from uuid import UUID
import app.petGui
import pandas as pd
from os.path import isdir, isfile
import pathlib
import shutil

from ..dto.session import backend, cookie, SessionData, verifier
from ..services.session import set_job_id, set_event, end_session

router = APIRouter()
templates = Jinja2Templates(directory="templates")

local = False  # If running app locally
ssh = "sshpass"
if local:
    ssh = "/opt/homebrew/bin/sshpass"

@router.get("/get_session")
async def get_session(request: Request):
    try:
        session = await backend.read(uuid.UUID(request.cookies["session"]))
    except KeyError:
        return None
    return session


@router.get("/start", response_class=HTMLResponse)
async def start(request: Request, session = Depends(get_session)):
    if session:
        return templates.TemplateResponse("start.html", {"request": request, "session": True})
    else:
        return templates.TemplateResponse("start.html", {"request": request, "session": False})


@router.get("/login")
async def login_form(request: Request, error=None, logout: bool = False, session=Depends(get_session)):
    if logout:
        return templates.TemplateResponse('login.html', {'request': request, 'error': error,
                                                         'logout_msg': "Logged out successfully!"})
    if session:
        return RedirectResponse(request.url_for("homepage"), status_code=303)
    else:
        return templates.TemplateResponse('login.html', {'request': request, 'error': error})



@router.post("/basic", name="homepage")
async def get_form(request: Request, sample: str = Form(...),
                   label: str = Form(...),
                   model_para: str = Form(...),
                   template_0: str = Form(...),
                   session=Depends(get_session)):
    print(session)
    id = hash(session.id)
    last_pos_file = session.last_pos_file
    log_file = session.log_file
    try:
        # Initialize last_pos to the value stored in last_pos.txt, or 0 if the file does not exist
        if os.path.exists(last_pos_file):
            with open(last_pos_file, "r") as file:
                os.environ[f"{id}_log"] = file.read()
        else:
            os.environ[f"{id}_log"] = str(0)
            f = os.open(log_file, os.O_CREAT)
            print(f)
            os.environ[f"{id}_inp"] = "False"
            print(os.environ[f"{id}_inp"])
        da = await request.form()
        da = jsonable_encoder(da)
        template_counter = 1
        origin_counter = 0
        mapping_counter = 0

        os.environ[f"{id}_medbert"] = "True" if model_para == "/prj/doctoral_letters/PETGUI/med_bert_local" else "False" #"GerMedBERT/medbert-512" else "False"

        para_dic = {"file": [direc for direc in os.listdir(f"{id}/data_uploaded")
                             if os.path.isdir(f"{id}/data_uploaded/{direc}")][0], "sample": sample,
                    "label": label, "delimiter": os.environ[f"{id}_delimiter"],
                    "template_0": template_0, "model_para": model_para}

        while f"template_{str(template_counter)}" in da:  # Template
            template_key = f"template_{str(template_counter)}"
            para_dic[template_key] = da[template_key]
            template_counter = template_counter + 1
        while f"origin_{str(origin_counter)}" in da:  # Label
            origin_key = f"origin_{str(origin_counter)}"
            para_dic[origin_key] = da[origin_key]
            origin_counter = origin_counter + 1
        while f"mapping_{str(mapping_counter)}" in da:  # Verbalizer
            mapping_key = f"mapping_{str(mapping_counter)}"
            para_dic[mapping_key] = da[mapping_key]
            mapping_counter = mapping_counter + 1
        print(para_dic)
        if f"{id}_unlabeled" in os.environ:
            para_dic["unlabeled"] = True

        with open(f'{id}/data.json', 'w') as f:
            json.dump(para_dic, f)
        redirect_url = request.url_for('logging')
        return RedirectResponse(redirect_url, status_code=303)
    except Exception as e:
        error = str(e)
        print(error)
        return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid folder structure: Please make sure your uploaded folder matches the specified format."})


@router.get("/basic", response_class=HTMLResponse, name='homepage')
def get_form(request: Request, message: str = None):
    try:
        pathlib.Path("static/chart.png").unlink()
    except:
        pass
    if message:
        return templates.TemplateResponse("index.html",
                                          {"request": request, "message": message})
    else:
        return templates.TemplateResponse("index.html", {"request": request})


@router.get("/logging", name="logging")
async def logging(request: Request, error: str = None):
    return templates.TemplateResponse("next.html", {"request": request, "error": error})


@router.get("/log", name="log")
async def read_log(session = Depends(get_session)):
    id = hash(session.id)
    last_pos_file = session.last_pos_file
    log_file = session.log_file
    with open(log_file, "r") as file:
        file.seek(int(os.environ[f"{id}_log"]))
        lines = file.readlines()
        os.environ[f"{id}_log"] = str(file.tell())
    with open(last_pos_file, "w") as file:
        file.write(os.environ[f"{id}_log"])
    info_lines = [line.strip() for line in lines if any(
        word in line for word in
        ["Creating", "Returning", "Saving", "Starting evaluation", "'acc'", "RESULT ", "Training Complete"])
                  or "input_ids" in line and os.environ[f"{id}_inp"] == "False"]

    info_lines = [line for line in info_lines if
                  line not in list(filter(lambda x: "input_ids" in x, info_lines))[1:]]
    if any(["input_ids" in line for line in info_lines]):
        os.environ[f"{id}_inp"] = "True"
        print(os.environ[f"{id}_inp"])
    return {"log": info_lines}


@router.get("/download", name="download")
def download(session=Depends(get_session)):
    id = hash(session.id)
    """
    Returns:
         final dict, e.g.: dict={p0-i0: {acc: 0.5, ...}, ...}
    """
    return FileResponse(f"{id}/results.json", filename="results.json")


@router.get("/final", response_class=HTMLResponse, name='final')
def get_final_template(request: Request, message: str = None, session=Depends(get_session)):
    if message:
        return templates.TemplateResponse("final_page.html",
                                          {"request": request, "message": message})
    else:
        return templates.TemplateResponse("final_page.html", {"request": request})

@router.post("/uploadfile/")
async def create_upload_file(session=Depends(get_session), file: UploadFile = File(...)):
    """
    Upload function for the final page
    """
    id = hash(session.id)
    upload_folder = f"{id}/data_uploaded/unlabeled"
    if os.path.exists(upload_folder):
        shutil.rmtree(upload_folder)
    os.makedirs(upload_folder)
    file_path = os.path.join(upload_folder, "unlabeled.txt")
    with open(file_path, "wb") as file_object:
        file_object.write(file.file.read())
    return {"filename": "unlabeled.txt", "path": file_path}


@router.get("/download_prediction", name="download_prediction")
def download_predict(session=Depends(get_session)):
    id = hash(session.id)
    with open(f'{id}/label_dict.json', 'r') as file:
        label_mapping = json.load(file)
    df = pd.read_csv(f"{id}/output/predictions.csv")

    # Convert the labels to string and map to the new labels
    df['label'] = df['label'].astype(str).map(label_mapping)

    # Save the updated dataframe
    df.to_csv(f"{id}/output/predictions.csv", index=False)
    return FileResponse(f"{id}/output/predictions.csv", filename="predictions.csv")


@router.get("/logout")
async def logout(response: Response, session=Depends(get_session)):
    event = session.event
    if not event:
        await set_event(session.id, session, True)   # Stop job threads
    await clean(session, logout=True)
    await end_session(cookie, response)
    response.delete_cookie(key="session")
    return {"Logout": "successful"}


@router.get("/clean", name="clean")
async def clean(session: SessionData = Depends(get_session), logout: bool = False, ssh=ssh):
    """
    Iterates over created paths during PET and unlinks them.
    Returns:
        redirection to homepage
    """
    user = session.username
    id = hash(session.id)
    remote_loc = session.remote_loc
    cluster_name = session.cluster_name
    log_file = session.log_file
    job_status = session.job_status
    job_id = session.job_id

    paths = ["logging.txt", "last_pos.txt", "output", "results.json", "data.json", "data_uploaded", "static/chart.png",
             "static/chart_prediction.png", "label_dict.json"]
    paths = [f"{id}/" + path if "png" not in path else path for path in paths]
    for path in paths if not logout else [f"{id}"]:
        file_path = pathlib.Path(path)
        if isfile(path):
            file_path.unlink()
        elif isdir(path):
            shutil.rmtree(path)
    if job_id:
        rm_cmd = [ssh, '-e', 'ssh',
                  f'{user}@{cluster_name}', f'rm -r {remote_loc} /home/{user}/{log_file.split("/")[-1]}']
        proc = subprocess.Popen(rm_cmd, env={"SSHPASS": os.environ[f"{id}"]}, shell=False, stdout=PIPE,
                                stderr=PIPE)
        outs, errs = proc.communicate()
        print(outs, errs)
        if job_status:
            await app.petGui.abort(session, True)
        await set_job_id(session.id, session, "")
    return {"Status": "Cleaned"}

