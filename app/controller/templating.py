from fastapi import Request, Depends, APIRouter, Form, File, UploadFile, Response, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.responses import FileResponse
from fastapi.encoders import jsonable_encoder
import json, os, tarfile, subprocess
from subprocess import PIPE
from uuid import UUID, uuid4

'''LDAP'''
from os.path import isdir, isfile
import pathlib
import shutil

from ..dto.session import SessionData, backend, cookie, verifier


router = APIRouter()

templates = Jinja2Templates(directory="templates")


local = False # If running app locally
ssh = "sshpass"
if local:
    ssh = "/opt/homebrew/bin/sshpass"





@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, error=None, logout: bool = False):
    if logout:
        return templates.TemplateResponse('login.html', {'request': request, 'error': error, 'logout_msg': "Logged out successfully!"})
    else:
        return templates.TemplateResponse('login.html', {'request': request, 'error': error})


@router.post("/basic", name="homepage", dependencies=[Depends(cookie)])
async def get_form(request: Request, sample: str = Form(media_type="multipart/form-data"),
                   label: str = Form(media_type="multipart/form-data"),
                   origin_0: str = Form(media_type="multipart/form-data"),
                   mapping_0: str = Form(media_type="multipart/form-data"),
                   origin_1: str = Form(media_type="multipart/form-data"),
                   mapping_1: str = Form(media_type="multipart/form-data"),
                   model_para: str = Form(media_type="multipart/form-data"),
                   file: UploadFile = File(...),
                   template_0: str = Form(media_type="multipart/form-data"),
                   session_id: UUID = Depends(cookie), session_data: SessionData = Depends(verifier)):
    try:

        await read_log(session_id, session_data, initial=True)
        try:
            file_upload = tarfile.open(fileobj=file.file, mode="r:gz")
            file_upload.extractall(f'{hash(session_id)}/data_uploaded')
        except:
            return templates.TemplateResponse('index.html', {'request': request, 'error': "Invalid File Type: Please upload your data as a zip file with the extension '.tar.gz'"})
        da = await request.form()
        da = jsonable_encoder(da)
        template_counter = 1
        origin_counter = 2
        mapping_counter = 2
        para_dic = {"file": "".join(next(os.walk(f"./{hash(session_id)}/data_uploaded/"))[1]), "sample": sample, "label": label,
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
        with open(f'{hash(session_id)}/data.json', 'w') as f:
            json.dump(para_dic, f)
        if origin_counter <2:
            return templates.TemplateResponse('index.html', {'request': request,
                                                             'error': "Please fill in all required parameters."})
        redirect_url = request.url_for('logging')
        print(para_dic)
        return RedirectResponse(redirect_url, status_code=303)

    except Exception as e:
        error = str(e)
        return templates.TemplateResponse("index.html", {"request": request, "error": error})


@router.get("/basic", response_class=HTMLResponse, name='homepage')
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/progress", response_class=HTMLResponse, name="progress")
def read_item(request: Request):
    max_num = 100
    return templates.TemplateResponse("progress.html", {"request": request, "max_num": max_num})

@router.get("/logging", name="logging", dependencies=[Depends(cookie)])
async def logging(request: Request, error: str = None):
    return templates.TemplateResponse("next.html", {"request": request, "error": error})


@router.get("/log", name="log", dependencies=[Depends(cookie)])
async def read_log(session_id: UUID = Depends(cookie), session_data: SessionData = Depends(verifier),
                   initial: bool = False):
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

        info_lines = [line for line in info_lines if line not in list(filter(lambda x: "input_ids" in x, info_lines))[1:]]
        if any(["input_ids" in line for line in info_lines]):
            os.environ[f"{hash(session_id)}_inp"] = "True"
        return {"log": info_lines}


@router.get("/download", name="download", dependencies=[Depends(cookie)])
def download(session_id: UUID = Depends(cookie)):
    """
    Returns:
         final dict, e.g.: dict={p0-i0: {acc: 0.5, ...}, ...}
    """
    return FileResponse(f"{hash(session_id)}/results.json", filename="results.json")

@router.get("/final", response_class=HTMLResponse, name='final', dependencies=[Depends(cookie)])
async def get_final_template(request: Request, error = None):
    return templates.TemplateResponse("final_page.html", {"request": request, "error": error})

@router.post("/uploadfile/", dependencies=[Depends(cookie)])
async def create_upload_file(file: UploadFile = File(...), session_id: UUID = Depends(cookie)):
    """
    Upload function for the final page
    """
    upload_folder = f"{hash(session_id)}/data_uploaded/unlabeled"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, file.filename)
    with open(file_path, "wb") as file_object:
        file_object.write(file.file.read())
    return {"filename": file.filename, "path": file_path}


@router.get("/download_prediction", name="download_prediction", dependencies=[Depends(cookie)])
def download_predict(session_id: UUID = Depends(cookie)):
    return FileResponse(f"{hash(session_id)}/output/predictions.csv", filename="predictions.csv")


@router.get("/logout")
def logout(request: Request, response: Response, session_id: UUID = Depends(cookie), session_data: SessionData = Depends(verifier)):
    clean(session_data, session_id, logout=True)
    cookie.delete_from_response(response)
    request.app.state.session = None


@router.get("/clean", name="clean", dependencies=[Depends(cookie)])
def clean(session_data: SessionData = Depends(verifier), session_id: UUID = Depends(cookie), logout: bool = False,ssh=ssh):
    """
    Iterates over created paths during PET and unlinks them.
    Returns:
        redirection to homepage
    """
    user = session_data.username
    remote_loc = session_data.remote_loc
    cluster_name = session_data.cluster_name
    log_file = session_data.log_file

    paths = ["logging.txt", "last_pos.txt", "output", "results.json", "data.json", "data_uploaded", "static/chart.png"]
    paths = [f"{hash(session_id)}/"+path for path in paths]
    for path in paths if not logout else [f"{hash(session_id)}"]:
        file_path = pathlib.Path(path)
        if isfile(path):
            file_path.unlink()
        elif isdir(path):
            shutil.rmtree(path)
    try:
        rm_cmd = [ssh, '-e', 'ssh',
                   f'{user}@{cluster_name}', f'rm -r {remote_loc} /home/{user}/{log_file.split("/")[-1]}']
        proc = subprocess.Popen(rm_cmd, env={"SSHPASS": os.environ[f"{hash(session_id)}"]}, shell=False, stdout=PIPE,
                                stderr=PIPE)
        outs, errs = proc.communicate()
        print(outs, errs)
    except:
        pass