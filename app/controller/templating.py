from fastapi import Request, Depends, APIRouter, Form, File, UploadFile, Response, HTTPException, FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.responses import FileResponse
from fastapi.encoders import jsonable_encoder
import json, os, tarfile, subprocess
from subprocess import PIPE
from uuid import UUID, uuid4
import threading
from threading import Event
import app.petGui
from ..dto.session import cookie
import pandas as pd
from os.path import isdir, isfile
import pathlib
import shutil

from ..services.session import SessionService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

local = False  # If running app locally
ssh = "sshpass"
if local:
    ssh = "/opt/homebrew/bin/sshpass"


def get_session_service(request: Request):
    try:
        return request.app.state.session
    except:
        return False


@router.get("/start", response_class=HTMLResponse)
def start(request: Request, session: SessionService = Depends(get_session_service)):
    if session:
        return templates.TemplateResponse("start.html", {"request": request, "session": True})
    else:
        return templates.TemplateResponse("start.html", {"request": request, "session": False})


@router.get("/login")
def login_form(request: Request, error=None, logout: bool = False,
               session: SessionService = Depends(get_session_service)):
    if logout:
        return templates.TemplateResponse('login.html', {'request': request, 'error': error,
                                                         'logout_msg': "Logged out successfully!"})
    elif session:
        try:
            session.get_session_id()
            return RedirectResponse(request.url_for("homepage"), status_code=303)
        except:
            return templates.TemplateResponse('login.html', {'request': request, 'error': error})
    else:
        return templates.TemplateResponse('login.html', {'request': request, 'error': error})


@router.post("/basic", name="homepage", dependencies=[Depends(get_session_service)])
async def get_form(request: Request, sample: str = Form(media_type="multipart/form-data"),
                   label: str = Form(media_type="multipart/form-data"),
                   model_para: str = Form(media_type="multipart/form-data"),
                   template_0: str = Form(media_type="multipart/form-data"),
                   session: SessionService = Depends(get_session_service)):
    session_id, session_data = session.get_session_id(), session.get_session_data()
    try:
        await read_log(session, initial=True)
        da = await request.form()
        da = jsonable_encoder(da)
        template_counter = 1
        origin_counter = 0
        mapping_counter = 0

        os.environ[f"{hash(session_id)}_medbert"] = "True" if model_para == "/prj/doctoral_letters/PETGUI/med_bert_local" else "False" #"GerMedBERT/medbert-512" else "False"

        para_dic = {"file": [direc for direc in os.listdir(f"{hash(session_id)}/data_uploaded")
                             if os.path.isdir(f"{hash(session_id)}/data_uploaded/{direc}")][0], "sample": sample,
                    "label": label, "delimiter": os.environ[f"{hash(session_id)}_delimiter"],
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

        redirect_url = request.url_for('logging')
        print(para_dic)
        if f"{hash(session_id)}_unlabeled" in os.environ:
            para_dic["unlabeled"] = True

        with open(f'{hash(session_id)}/data.json', 'w') as f:
            json.dump(para_dic, f)

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


@router.get("/progress", response_class=HTMLResponse, name="progress")
def read_item(request: Request):
    max_num = 100
    return templates.TemplateResponse("progress.html", {"request": request, "max_num": max_num})


@router.get("/logging", name="logging", dependencies=[Depends(get_session_service)])
async def logging(request: Request, error: str = None, session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()
    return templates.TemplateResponse("next.html", {"request": request, "error": error})


@router.get("/log", name="log", dependencies=[Depends(get_session_service)])
async def read_log(session: SessionService = Depends(get_session_service), initial: bool = False):
    session_id, session_data = session.get_session_id(), session.get_session_data()
    last_pos_file = session_data.last_pos_file
    log_file = session_data.log_file
    if initial:
        # Initialize last_pos to the value stored in last_pos.txt, or 0 if the file does not exist
        if os.path.exists(last_pos_file):
            with open(last_pos_file, "r") as file:
                os.environ[f"{hash(session_id)}_log"] = file.read()
        else:
            os.environ[f"{hash(session_id)}_log"] = str(0)
            f = os.open(log_file, os.O_CREAT)
            os.environ[f"{hash(session_id)}_inp"] = "False"
            print(os.environ[f"{hash(session_id)}_inp"])
    else:
        with open(log_file, "r") as file:
            file.seek(int(os.environ[f"{hash(session_id)}_log"]))
            lines = file.readlines()
            os.environ[f"{hash(session_id)}_log"] = str(file.tell())
        with open(last_pos_file, "w") as file:
            file.write(os.environ[f"{hash(session_id)}_log"])
        info_lines = [line.strip() for line in lines if any(
            word in line for word in
            ["Creating", "Returning", "Saving", "Starting evaluation", "'acc'", "RESULT ", "Training Complete"])
                      or "input_ids" in line and os.environ[f"{hash(session_id)}_inp"] == "False"]

        info_lines = [line for line in info_lines if
                      line not in list(filter(lambda x: "input_ids" in x, info_lines))[1:]]
        if any(["input_ids" in line for line in info_lines]):
            os.environ[f"{hash(session_id)}_inp"] = "True"
            print(os.environ[f"{hash(session_id)}_inp"])
        return {"log": info_lines}


@router.get("/download", name="download", dependencies=[Depends(get_session_service)])
def download(session: SessionService = Depends(get_session_service)):
    """
    Returns:
         final dict, e.g.: dict={p0-i0: {acc: 0.5, ...}, ...}
    """
    session_id = session.get_session_id()
    return FileResponse(f"{hash(session_id)}/results.json", filename="results.json")


@router.get("/final", response_class=HTMLResponse, name='final', dependencies=[Depends(get_session_service)])
def get_final_template(request: Request, message: str = None):
    if message:
        return templates.TemplateResponse("final_page.html",
                                          {"request": request, "message": message})
    else:
        return templates.TemplateResponse("final_page.html", {"request": request})


@router.post("/uploadfile/", dependencies=[Depends(get_session_service)])
async def create_upload_file(file: UploadFile = File(...), session: SessionService = Depends(get_session_service)):
    """
    Upload function for the final page
    """
    session_id = session.get_session_id()
    upload_folder = f"{hash(session_id)}/data_uploaded/unlabeled"
    if os.path.exists(upload_folder):
        shutil.rmtree(upload_folder)
    os.makedirs(upload_folder)
    file_path = os.path.join(upload_folder, "unlabeled.txt")
    with open(file_path, "wb") as file_object:
        file_object.write(file.file.read())
    return {"filename": "unlabeled.txt", "path": file_path}


@router.get("/download_prediction", name="download_prediction", dependencies=[Depends(get_session_service)])
def download_predict(session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()
    with open(f'{hash(session_id)}/label_dict.json', 'r') as file:
        label_mapping = json.load(file)
    df = pd.read_csv(f"{hash(session_id)}/output/predictions.csv")

    # Convert the labels to string and map to the new labels
    df['label'] = df['label'].astype(str).map(label_mapping)

    # Save the updated dataframe
    df.to_csv(f"{hash(session_id)}/output/predictions.csv", index=False)
    return FileResponse(f"{hash(session_id)}/output/predictions.csv", filename="predictions.csv")


@router.get("/logout")
async def logout(request: Request, response: Response, session: SessionService = Depends(get_session_service)):
    if request.app.state.event:
        request.app.state.event.set()   # Stop job threads
        request.app.state.event = None
    await clean(request, session, logout=True)
    cookie.delete_from_response(response)
    request.app.state.session = None


@router.get("/clean", name="clean", dependencies=[Depends(get_session_service)])
async def clean(request: Request, session: SessionService = Depends(get_session_service), logout: bool = False, ssh=ssh):
    """
    Iterates over created paths during PET and unlinks them.
    Returns:
        redirection to homepage
    """
    session_id, session_data = session.get_session_id(), session.get_session_data()
    user = session_data.username
    remote_loc = session_data.remote_loc
    cluster_name = session_data.cluster_name
    log_file = session_data.log_file

    paths = ["logging.txt", "last_pos.txt", "output", "results.json", "data.json", "data_uploaded", "static/chart.png"]
    paths = [f"{hash(session_id)}/" + path for path in paths]
    for path in paths if not logout else [f"{hash(session_id)}"]:
        file_path = pathlib.Path(path)
        if isfile(path):
            file_path.unlink()
        elif isdir(path):
            shutil.rmtree(path)
    if request.app.state.job_id:
        rm_cmd = [ssh, '-e', 'ssh',
                  f'{user}@{cluster_name}', f'rm -r {remote_loc} /home/{user}/{log_file.split("/")[-1]}']
        proc = subprocess.Popen(rm_cmd, env={"SSHPASS": os.environ[f"{hash(session_id)}"]}, shell=False, stdout=PIPE,
                                stderr=PIPE)
        outs, errs = proc.communicate()
        print(outs, errs)
        await app.petGui.run(request, session)
        request.app.state.job_id = None
