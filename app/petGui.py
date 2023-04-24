from fastapi import FastAPI, File, Form, UploadFile, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import tarfile
import json
import os
from os.path import isdir, isfile
import pathlib
import shutil
from fastapi.encoders import jsonable_encoder
from ldap3 import Server, Connection, ALL, Tls, AUTO_BIND_TLS_BEFORE_BIND, core
from ssl import PROTOCOL_TLSv1_2
import threading
import subprocess
from subprocess import Popen, PIPE
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
    remote_loc: str
    remote_loc_pet: str
    cluster_name = 'cluster.dieterichlab.org'



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


app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/steps", name="steps", dependencies=[Depends(cookie)])
def get_steps(session_id: UUID = Depends(cookie)):
    with open(f"./{hash(session_id)}/data.json") as f:
        data = json.load(f)
    count_tmp = len([tmp for tmp in data.keys() if "template_" in tmp])
    count_steps = 18 + (count_tmp-1) * 5
    return {"steps": count_steps}

@app.get("/", name="start")
def main():
    return RedirectResponse(url="/login")
  

@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(request: Request, session_id: UUID = Depends(cookie)):
    return who(session_id)
    #return RedirectResponse(request.url_for("who"), status_code=303)

@app.get("/who", dependencies=[Depends(cookie)], name="who")
def who(session_id: UUID = Depends(cookie)):
    return session_id

@app.get("/logout", dependencies=[Depends(cookie)])
def logout(response: Response, session_id: UUID = Depends(cookie), session_data: SessionData = Depends(verifier)):
    clean(session_data, session_id, logout=True)
    cookie.delete_from_response(response)
    return {"Logout", "successful"}



LDAP_SERVER = 'ldap://ldap2.dieterichlab.org'
CA_FILE = 'DieterichLab_CA.pem'
USER_BASE = 'dc=dieterichlab,dc=org'
LDAP_SEARCH_FILTER = '({name_attribute}={name})'


def authenticate_ldap(username: str, password: str):
    try:
        tls = Tls(ca_certs_file=CA_FILE, version=PROTOCOL_TLSv1_2)
        server = Server(LDAP_SERVER, get_info=ALL, tls=tls)
        conn = Connection(server, auto_bind=AUTO_BIND_TLS_BEFORE_BIND, raise_exceptions=True)
        conn.bind()
        conn.search(USER_BASE, LDAP_SEARCH_FILTER.format(name_attribute="uid", name=username))
        if conn.result['result'] == 0:
            user_dn = conn.response[0]['dn']
            try:
                conn = Connection(server, user_dn, password, auto_bind=AUTO_BIND_TLS_BEFORE_BIND)
                return True
            except core.exceptions.LDAPBindError:
                print("User authentication failed.")
                return False
        else:
            return False
    except Exception as e:
        print(str(e))
        return False


#Endpoint to render login form
@app.get('/login', response_class=HTMLResponse)
async def login_form(request: Request, error=None):
    return templates.TemplateResponse('login.html', {'request': request, 'error': error})

async def create_session(user: str, response: Response):

    session = uuid4()
    remote_loc = f'/home/{user}/{hash(session)}/'
    remote_loc_pet = f'/home/{user}/{hash(session)}/pet/'
    data = SessionData(username=user, remote_loc=remote_loc, remote_loc_pet=remote_loc_pet)
    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    return session

# Endpoint to authenticate users
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not authenticate_ldap(username=username, password=password):
        error = 'Invalid username or password'
        return templates.TemplateResponse('login.html', {'request': request, 'error': error})
    os.environ[f"{username}"] = password
    response = RedirectResponse(url=request.url_for("homepage"), status_code=303)
    session_uuid = await create_session(username, response)
    os.makedirs(f"./{hash(session_uuid)}", exist_ok=True)  # If run with new conf.
    return response

@app.get("/logging/start_train", dependencies=[Depends(cookie)])
async def run(session_data: SessionData = Depends(verifier), session_id: UUID = Depends(cookie)):
    """
    Kicks off PET by calling train method.
    """
    '''Start PET'''
    job_id = await submit_job(session_data, False, session_id)
    t = threading.Thread(target=check_job_status, args=(job_id, session_data, False, session_id))
    t.start()

async def submit_job(session_data, predict: bool = False, session_id: UUID = Depends(cookie)):
    # Copy the SLURM script file to the remote cluster
    print("Submitting job..")

    user = session_data.username
    remote_loc = session_data.remote_loc
    remote_loc_pet = session_data.remote_loc_pet
    cluster_name = session_data.cluster_name

    if predict:
        scp_cmd = ['sshpass', '-e', 'scp', '-r', f'{str(hash(session_id))}/data_uploaded/unlabeled',
                   f'{user}@{cluster_name}:{remote_loc_pet.format(user=user)}data_uploaded/']
        outs, errs = bash_cmd(scp_cmd, user)
        ssh_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                   f'sbatch {remote_loc_pet.format(user=user)}predict.sh {remote_loc.split("/")[-2]}']
        outs, errs = bash_cmd(ssh_cmd, user)
        print("Prediction: ", outs)
        # Get the job ID from the output of the sbatch command
        job_id = outs.decode('utf-8').strip().split()[-1]
        return job_id
    else:
        mkdir_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}', f'mkdir {remote_loc}']
        outs, errs = bash_cmd(mkdir_cmd, user)
        dir = hash(session_id)

        files = ["pet", "data.json", "train.sh", "data_uploaded", "predict.sh"]
        files = [str(dir)+"/"+f if f == "data.json" or f == "data_uploaded" else f for f in files]
        print(files)
        for f in files:
            scp_cmd = ['sshpass', '-e', 'scp', '-r', f,
                   f'{user}@{cluster_name}:{remote_loc.format(user = user)}' if "pet" in f
                   else f'{user}@{cluster_name}:{remote_loc_pet.format(user = user)}']
            outs, errs = bash_cmd(scp_cmd, user)
            print(outs, errs)

        # Submit the SLURM job via SSH
        ssh_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                   f'sbatch {remote_loc_pet.format(user=user)}train.sh {remote_loc.split("/")[-2]}']
        outs, errs = bash_cmd(ssh_cmd, user)
        # Get the job ID from the output of the sbatch command
        job_id = outs.decode('utf-8').strip().split()[-1]
        return job_id

def bash_cmd(cmd, user, shell:bool = False):
    proc = subprocess.Popen(" ".join(cmd) if shell else cmd, env={"SSHPASS": os.environ[f"{user}"]}, shell=shell,
                            stdout=subprocess.PIPE, stderr=PIPE)
    outs, errs = proc.communicate()
    return outs, errs


def check_job_status(job_id: str, session_data: SessionData = Depends(verifier), predict: bool = False,
                     session_id: UUID = Depends(cookie)):
    user = session_data.username
    remote_loc_pet = session_data.remote_loc_pet
    cluster_name = session_data.cluster_name
    while True:
        cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}', f"squeue -j {job_id} -h -t all | awk '{{print $5}}'"]
        outs, errs = bash_cmd(cmd, user)
        status = outs.decode("utf-8").strip().split()[-1]
        print(status)
        if status == "R":
            pass
        elif status == "CD":
            if predict:
                scp_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                           f'cat {remote_loc_pet.format(user=user)}predictions.csv', f'> {hash(session_id)}/output/predictions.csv']
                outs, errs = bash_cmd(scp_cmd, user, shell=True)
                print(outs, errs)
                return {"status": "finished"}
            else:
                with open(f'{hash(session_id)}/logging.txt', 'a') as file:
                    file.write('Training Complete\n')
                ssh_cmd = ['sshpass', '-e', 'ssh',
                           f'{user}@{cluster_name}', f'cd {remote_loc_pet.format(user=user)} '
                                                     f'&& find . -name "results.json" -type f']
                outs, errs = bash_cmd(ssh_cmd, user)
                print(outs, errs)
                files = outs.decode("utf-8")
                for f in files.rstrip().split("\n"):
                    f = f.lstrip("./")
                    os.makedirs(f"{hash(session_id)}/{f.rstrip('results.json')}", exist_ok=True)
                    while not os.path.exists(f"{hash(session_id)}/{f.rstrip('results.json')}"):
                        time.sleep(1)
                    scp_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                               f'cat {remote_loc_pet.format(user=user)}{f} > {hash(session_id)}/{f}']
                    outs, errs = bash_cmd(scp_cmd, user, shell=True)
                    print(outs, errs)
                '''Call Results'''
                results(session_id)
                return {"Pet": "finished"}

        time.sleep(5)

        ssh_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                   f'cat /home/{user}{log_file.format(session_id="")}']
        outs, errs = bash_cmd(ssh_cmd, user)
        log_contents = outs.decode('utf-8')

        # Update the log file on the local machine
        with open(f"{log_file.format(session_id=hash(session_id))}", 'w') as f:
            f.write(log_contents)


@app.get("/logging", name="logging", dependencies=[Depends(cookie)])
async def logging(request: Request):
    return templates.TemplateResponse("next.html", {"request": request})


@app.get("/final", response_class=HTMLResponse, name='final', dependencies=[Depends(cookie)])
async def get_final_template(request: Request):
    return templates.TemplateResponse("final_page.html", {"request": request})


@app.get("/results", dependencies=[Depends(cookie)])
def results(session_id: UUID = Depends(cookie)):
    """
    Saves results.json for each pattern-iteration pair of output/final directory in a dictionary.
    Returns:
        html page with results & homepage redirection buttons
    """
    dirs = next(os.walk(f"{hash(session_id)}/output/"))[1]
    scores = {}
    for d in dirs:
        final = ""
        if "final" in d:
            k = "Final"
            scores[k] = {"acc": "-", "pre-rec-f1-supp": []}
            finals = next(os.walk(f"{hash(session_id)}/output/final/"))[1]
            assert len(finals) == 1
            final += f"/{finals[0]}"
        else:
            k = f"Pattern-{int(d[1])+1} Iteration 1"
            scores[k] = {"acc": "-", "pre-rec-f1-supp": []}
            final = ""
        with open(f"{hash(session_id)}/output/{d}{final}/results.json") as f:
            json_scores = json.load(f)
            acc = round(json_scores["test_set_after_training"]["acc"], 2)
            pre, rec, f1, supp = json_scores["test_set_after_training"]["pre-rec-f1-supp"]
            labels = [i for i in range(len(pre))]
            for l in labels:
                scores[k]["pre-rec-f1-supp"].append(f"Label: {l} Pre: {round(pre[l], 2)}, Rec: {round(rec[l], 2)},"
                                                    f"F1: {round(f1[l], 2)}, Supp: {supp[0]}")
            scores[k]["acc"] = acc
            #scores[k]["pre-rec-f1-supp"] = [round(float(scr), 2) for l in scores.values() for scr in l]

    with open(f"{hash(session_id)}/results.json", "w") as res:
        json.dump(scores, res)
        

@app.get("/download", name="download", dependencies=[Depends(cookie)])
def download(session_id: UUID = Depends(cookie)):
    """
    Returns:
         final dict, e.g.: dict={p0-i0: {acc: 0.5, ...}, ...}
    """
    return FileResponse(f"{hash(session_id)}/results.json", filename="results.json")


@app.get("/download_prediction", name="download_prediction", dependencies=[Depends(cookie)])
def download_predict(session_id: UUID = Depends(cookie)):
    return FileResponse(f"{hash(session_id)}/output/predictions.csv", filename="predictions.csv")


@app.get("/clean", name="clean", dependencies=[Depends(cookie)])
def clean(session_data: SessionData = Depends(verifier), session_id: UUID = Depends(cookie), logout: bool = False):
    """
    Iterates over created paths during PET and unlinks them.
    Returns:
        redirection to homepage
    """
    user = session_data.username
    remote_loc = session_data.remote_loc
    cluster_name = session_data.cluster_name

    paths = ["logging.txt", "last_pos.txt", "output", "results.json", "data.json", "data_uploaded"]
    paths = [f"{hash(session_id)}/"+path for path in paths]
    for path in paths if not logout else [f"{hash(session_id)}"]:
        file_path = pathlib.Path(path)
        if isfile(path):
            file_path.unlink()
        elif isdir(path):
            shutil.rmtree(path)
    try:
        rm_cmd = ['sshpass', '-e', 'ssh',
                   f'{user}@{cluster_name}', f'rm -r {remote_loc.format(user=user)}']
        proc = subprocess.Popen(rm_cmd, env={"SSHPASS": os.environ[f"{user}"]}, shell=False, stdout=PIPE,
                                stderr=PIPE)
        outs, errs = proc.communicate()
        print(outs, errs)
    except:
        pass


@app.get("/basic", response_class=HTMLResponse, name='homepage')
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/progress", response_class=HTMLResponse, name="progress")
def read_item(request: Request):
    max_num = 100
    return templates.TemplateResponse("progress.html", {"request": request, "max_num": max_num})


@app.post("/uploadfile/", dependencies=[Depends(cookie)])
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


log_file = "{session_id}/logging.txt"


@app.get("/log", name = "log", dependencies=[Depends(cookie)])
async def read_log(session_id: UUID = Depends(cookie), initial: bool = False):
    if initial:
        # Initialize last_pos to the value stored in last_pos.txt, or 0 if the file does not exist
        if os.path.exists(last_pos_file):
            with open(last_pos_file.format(session_id=hash(session_id)), "r") as file:
                os.environ[f"{hash(session_id)}"] = file.read()
        else:
            os.environ[f"{hash(session_id)}"] = str(0)
            f = os.open(log_file.format(session_id=hash(session_id)), os.O_CREAT)
            os.environ[f"{hash(session_id)}_inp"] = "False"
    else:
        with open(log_file.format(session_id=hash(session_id)), "r") as file:
            file.seek(int(os.environ[f"{hash(session_id)}"]))
            lines = file.readlines()
            os.environ[f"{hash(session_id)}"] = str(file.tell())
        with open(last_pos_file.format(session_id=hash(session_id)), "w") as file:
            file.write(os.environ[f"{hash(session_id)}"])
        info_lines = [line.strip() for line in lines if any(
            word in line for word in
            ["Creating", "Returning", "Saving", "Starting evaluation", "'acc'", "RESULT ", "Training Complete"])
                      or "input_ids" in line and os.environ[f"{hash(session_id)}_inp"] == "False"]

        info_lines = [line for line in info_lines if line not in list(filter(lambda x: "input_ids" in x, info_lines))[1:]]
        if any(["input_ids" in line for line in info_lines]):
            os.environ[f"{hash(session_id)}_inp"] = "True"
        return {"log": info_lines}


last_pos_file = "{session_id}/last_pos.txt"


@app.post("/basic", name="homepage", dependencies=[Depends(cookie)])
async def get_form(request: Request, sample: str = Form(media_type="multipart/form-data"),
                   label: str = Form(media_type="multipart/form-data"),
                   origin_0: str = Form(media_type="multipart/form-data"),
                   mapping_0: str = Form(media_type="multipart/form-data"),
                   origin_1: str = Form(media_type="multipart/form-data"),
                   mapping_1: str = Form(media_type="multipart/form-data"),
                   model_para: str = Form(media_type="multipart/form-data"),
                   file: UploadFile = File(...),
                   template_0: str = Form(media_type="multipart/form-data"),
                   session_id: UUID = Depends(cookie)):
    await read_log(session_id, initial=True)
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


@app.get("/final/start_prediction", dependencies=[Depends(cookie)])
async def label_prediction(session_data: SessionData = Depends(verifier), session_id: UUID = Depends(cookie)):
    '''Start Predict'''
    job_id = await submit_job(session_data, True, session_id)
    return check_job_status(job_id, session_data, True, session_id)
