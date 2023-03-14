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
from ldap3 import Server, Connection, ALL, Tls, AUTO_BIND_TLS_BEFORE_BIND
from ssl import PROTOCOL_TLSv1_2
from Pet.examples import custom_task_pvp, custom_task_processor, custom_task_metric
import threading
import subprocess
import time
from pydantic import BaseModel
from fastapi import HTTPException, FastAPI, Response, Depends
from uuid import UUID, uuid4

from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
import atexit

class SessionData(BaseModel):
    username: str


cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)
backend = InMemoryBackend[UUID, SessionData]()


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)

################ START ##################
app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data.username


LDAP_SERVER = 'ldap://ldap2.dieterichlab.org'
CA_FILE = 'DieterichLab_CA.pem'
USER_BASE = 'dc=dieterichlab,dc=org'
LDAP_SEARCH_FILTER = '({name_attribute}={name})'


def authenticate_ldap(username: str) -> bool:
    try:
        tls = Tls(ca_certs_file=CA_FILE, version=PROTOCOL_TLSv1_2)
        server = Server(LDAP_SERVER, get_info=ALL, tls=tls)
        conn = Connection(server, auto_bind=AUTO_BIND_TLS_BEFORE_BIND, raise_exceptions=True)
        conn.bind()
        conn.search(USER_BASE, LDAP_SEARCH_FILTER.format(name_attribute="uid", name=username))
        if len(conn.entries) == 1:
            return True
        else:
            return False
    except Exception as e:
        print(str(e))
        return False


#Endpoint to render login form
@app.get('/login', response_class=HTMLResponse)
async def login_form(request: Request, error=None):
    return templates.TemplateResponse('login.html', {'request': request, 'error': error})

async def create_session(name: str, response: Response):

    session = uuid4()
    data = SessionData(username=name)
    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    print(session)


# Endpoint to authenticate users
@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    if not authenticate_ldap(username=username):
        error = 'Invalid username or password'
        return templates.TemplateResponse('login.html', {'request': request, 'error': error})
    response = RedirectResponse(url=request.url_for("homepage"), status_code=303)
    await create_session(username, response)
    return response

@app.get("/logging/start_train", dependencies=[Depends(cookie)])
async def run(session_data: SessionData = Depends(verifier)):
    """
    Kicks off PET by calling train method.
    """
    '''Start PET'''
    t = threading.Thread(target=submit_job, args=(session_data,))
    t.start()


# Set the SLURM cluster name or IP address
cluster_name = 'cluster.dieterichlab.org'
ssh_key = '~/.ssh/id_rsa'
remote_loc = '/home/{user}/'
remote_loc_pet = '/home/{user}/pet/'


def submit_job(session_data):
    # Copy the SLURM script file to the remote cluster
    print("Submitting job..")
    user = session_data.username
    files = ["pet", "data.json", "script.sh", "data_uploaded"]
    for f in files:
        if f != "pet":
            loc = remote_loc_pet
        else:
            loc = remote_loc
        scp_cmd = ['scp', '-r', '-i', ssh_key, f,
               f'{user}@{cluster_name}:{loc.format(user = user)}']
        try:
            subprocess.run(scp_cmd, check=True)
        except:
            choice = input(f"Connection to server {cluster_name} failed. \nRetry? (y)es/(n)o?")
            if choice.lower() in any(["yes", "y"]):
                subprocess.run(scp_cmd, check=True)
            else:
                print("Stopping process..")
                os.kill(os.getpid(), 15)

    # Submit the SLURM job via SSH
    ssh_cmd = ['ssh', '-i', ssh_key, f'{user}@{cluster_name}',
               f'sbatch {remote_loc_pet.format(user=user)}script.sh']
    submit_process = subprocess.run(ssh_cmd, check=True, capture_output=True)
    # Get the job ID from the output of the sbatch command
    job_id = submit_process.stdout.decode('utf-8').strip().split()[-1]
    check_job_status(job_id, session_data)


def check_job_status(job_id: str, session_data: SessionData = Depends(verifier)):
    user = session_data.username
    while True:
        cmd = ['ssh', '-i', ssh_key, f'{user}@{cluster_name}', f"squeue -j {job_id} -h -t all | awk '{{print $5}}'"]
        status = subprocess.check_output(cmd, shell=False).decode().strip()
        if status == "R":
            pass
        elif status == "CD":
            with open('logging.txt', 'a') as file:
                file.write('Training Complete\n')
            ssh_cmd = ['ssh', '-i', ssh_key,
                       f'{user}@{cluster_name}', f'cd {remote_loc_pet.format(user=user)}',
                       f'&& find . -name "results.json" -type f']
            files = subprocess.run(ssh_cmd, check=True, capture_output=True)
            files = files.stdout.decode("utf-8")
            for f in files.split("\n"):
                scp_cmd = ['rsync', '--relative', f'{user}@{cluster_name}:{remote_loc_pet.format(user=user)}{f}', '.']
                subprocess.run(scp_cmd, check=True)

            '''Call Results'''
            results()
            return {"status": "finished"}

        time.sleep(5)

        ssh_cmd = ['ssh', '-i', ssh_key, f'{user}@{cluster_name}',
                   f'cat {remote_loc.format(user=user)}{log_file}']
        log_process = subprocess.run(ssh_cmd, check=True, capture_output=True)
        log_contents = log_process.stdout.decode('utf-8')

        # Update the log file on the local machine
        with open(f"{log_file}", 'w') as f:
            f.write(log_contents)

@app.get("/logging", name="logging", dependencies=[Depends(cookie)])
async def logging(request: Request):
    return templates.TemplateResponse("next.html", {"request": request})


@app.get("/final", response_class=HTMLResponse, name='final', dependencies=[Depends(cookie)])
async def get_final_template(request: Request):
    return templates.TemplateResponse("final_page.html", {"request": request})

@app.get("/", name="start")
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
def clean(request: Request = None):
    """
    Iterates over created paths during PET and unlinks them.
    Returns:
        redirection to homepage
    """
    #paths = ["results.json", "data.json", "output", "Pet/data_uploaded", "templates/run.html", "last_pos.txt"]
    paths = ["logging.txt", "last_pos.txt", "output"]
    for path in paths:
        file_path = pathlib.Path(path)
        if isfile(path):
            file_path.unlink()
        elif isdir(path):
            shutil.rmtree(path)
    if request:
        url = request.url_for("homepage")
        return RedirectResponse(url, status_code=303)

atexit.register(clean)

@app.get("/basic", response_class=HTMLResponse, name='homepage')
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/progress", response_class=HTMLResponse, name="progress")
def read_item(request: Request):
    max_num = 100
    return templates.TemplateResponse("progress.html", {"request": request, "max_num": max_num})



@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    """
    Upload function for the final page
    """

    upload_folder = "./data_uploaded/unlabeled"
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
    file_upload.extractall('./data_uploaded')
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
