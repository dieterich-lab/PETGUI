from fastapi import FastAPI, Depends, UploadFile, File, Request, Response, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import json
import os
import threading
import time
import tarfile
import subprocess
from subprocess import PIPE
import pandas as pd
import matplotlib.pyplot as plt
from uuid import UUID, uuid4

'''LDAP'''
from ldap3 import Server, Connection, ALL, Tls, AUTO_BIND_TLS_BEFORE_BIND, core
from ssl import PROTOCOL_TLSv1_2

from app.controller import templating
from app.dto.session import SessionData, UUID
from .services.session import SessionService



'''START APP'''
app = FastAPI()
'''Include routers'''
app.include_router(templating.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not authenticate_ldap(username=username, password=password):
        error = 'Invalid username or password'
        return await templating.login_form(request, error)
    response = RedirectResponse(url=request.url_for("homepage"), status_code=303)
    global sessionObj
    sessionObj = await create_session(username, response)
    session_uuid = sessionObj.get_session_id()
    os.environ[f"{hash(session_uuid)}"] = password
    os.makedirs(f"./{hash(session_uuid)}", exist_ok=True)  # If run with new conf.
    return response


def authenticate_ldap(username: str, password: str):
    LDAP_SERVER = 'ldap://ldap2.dieterichlab.org'
    CA_FILE = 'DieterichLab_CA.pem'
    USER_BASE = 'dc=dieterichlab,dc=org'
    LDAP_SEARCH_FILTER = '({name_attribute}={name})'
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


async def create_session(user: str, response: Response):
    session_id = uuid4()
    remote_loc = f"/home/{user}/{hash(session_id)}/"
    remote_loc_pet = f"/home/{user}/{hash(session_id)}/pet/"
    cluster_name = "cluster.dieterichlab.org"
    log_file = f"{hash(session_id)}/logging.txt"
    last_pos_file = f"{hash(session_id)}/last_pos.txt"
    data = SessionData(username=user, remote_loc=remote_loc, remote_loc_pet=remote_loc_pet, cluster_name=cluster_name,
                       log_file=log_file, last_pos_file=last_pos_file)
    sessionObj = SessionService(data, session_id)
    await sessionObj.create_backend()
    sessionObj.create_cookie(response=response)
    return sessionObj


@app.get("/steps", name="steps", dependencies=[Depends(sessionObj.get_session_id)])
def get_steps(session_id: UUID = Depends(sessionObj.get_session_id)):
    with open(f"./{hash(session_id)}/data.json") as f:
        data = json.load(f)
    count_tmp = len([tmp for tmp in data.keys() if "template_" in tmp])
    count_steps = 18 + (count_tmp-1) * 5
    return {"steps": count_steps}


@app.get("/", name="start")
def main():
    return RedirectResponse(url="/login")


@app.get("/whoami", dependencies=[Depends(sessionObj.get_session_id), Depends(sessionObj.get_session_data)], name="whoami")
def whoami(session_id: UUID = Depends(sessionObj.get_session_id), session_data: SessionData = Depends(sessionObj.get_session_data)):
    return session_id, session_data


@app.get("/logging/start_train",  dependencies=[Depends(sessionObj.get_session_id), Depends(sessionObj.get_session_data)])
async def run(session_id: UUID = Depends(sessionObj.get_session_id), session_data: SessionData = Depends(sessionObj.get_session_data)):
    """
    Kicks off PET by calling train method.
    """
    '''Start PET'''
    print("Training starting..")
    job_id = await submit_job(session_data, False, session_id)
    t = threading.Thread(target=check_job_status, args=(job_id, session_data, False, session_id))
    t.start()


@app.get("/final/start_prediction", dependencies=[Depends(sessionObj.get_session_id), Depends(sessionObj.get_session_data)])
async def label_prediction(request: Request, session_data: SessionData = Depends(sessionObj.get_session_data),
                           session_id: UUID = Depends(sessionObj.get_session_id)):
    '''Start Predicttion'''
    try:
        print("Prediction starting..")
        job_id = await submit_job(session_data, True, session_id)
        return check_job_status(job_id, session_data, True, session_id)
    except Exception as e:
        error = "Something went wrong, please reload the page and try again"
        return await templating.get_final_template(request, error)


async def submit_job(session_data: SessionData = Depends(sessionObj.get_session_data), predict: bool = False,
                     session_id: UUID = Depends(sessionObj.get_session_id)):
    # Copy the SLURM script file to the remote cluster
    print("Submitting job..")

    user = session_data.username
    remote_loc = session_data.remote_loc
    remote_loc_pet = session_data.remote_loc_pet
    cluster_name = session_data.cluster_name

    if predict:
        try:
            scp_cmd = ['sshpass', '-e', 'scp', '-r', f'{str(hash(session_id))}/data_uploaded/unlabeled',
                       f'{user}@{cluster_name}:{remote_loc_pet}data_uploaded/']
            outs, errs = bash_cmd(scp_cmd, session_id)
            ssh_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                       f'sbatch {remote_loc_pet}predict.sh {remote_loc.split("/")[-2]}']
            outs, errs = bash_cmd(ssh_cmd, session_id)
            print("Prediction: ", outs)
            # Get the job ID from the output of the sbatch command
            job_id = outs.decode('utf-8').strip().split()[-1]
            return job_id
        except Exception as e:
            raise e
    else:
        mkdir_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}', f'mkdir {remote_loc}']
        outs, errs = bash_cmd(mkdir_cmd, session_id)
        dir = hash(session_id)

        files = ["pet", "data.json", "train.sh", "data_uploaded", "predict.sh"]
        files = [str(dir)+"/"+f if f == "data.json" or f == "data_uploaded" else f for f in files]
        print(files)
        for f in files:
            scp_cmd = ['sshpass', '-e', 'scp', '-r', f,
                   f'{user}@{cluster_name}:{remote_loc}' if "pet" in f
                   else f'{user}@{cluster_name}:{remote_loc_pet}']
            outs, errs = bash_cmd(scp_cmd, session_id)
            print(outs, errs)

        # Submit the SLURM job via SSH
        ssh_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                   f'sbatch {remote_loc_pet}train.sh {remote_loc.split("/")[-2]}']
        outs, errs = bash_cmd(ssh_cmd, session_id)
        # Get the job ID from the output of the sbatch command
        job_id = outs.decode('utf-8').strip().split()[-1]
        return job_id

def bash_cmd(cmd, session_id: UUID = Depends(sessionObj.get_session_id), shell:bool = False):
    proc = subprocess.Popen(" ".join(cmd) if shell else cmd, env={"SSHPASS": os.environ[f"{hash(session_id)}"]}, shell=shell,
                            stdout=subprocess.PIPE, stderr=PIPE)
    outs, errs = proc.communicate()
    return outs, errs


def check_job_status(job_id: str, session_data: SessionData = Depends(sessionObj.get_session_data), predict: bool = False,
                     session_id: UUID = Depends(sessionObj.get_session_id)):
    user = session_data.username
    remote_loc_pet = session_data.remote_loc_pet
    cluster_name = session_data.cluster_name
    log_file = session_data.log_file
    while True:
        cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}', f"squeue -j {job_id} -h -t all | awk '{{print $5}}'"]
        outs, errs = bash_cmd(cmd, session_id)
        status = outs.decode("utf-8").strip().split()[-1]
        print(status)
        if status == "R":
            pass
        elif status == "CD":
            if predict:
                scp_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                           f'cat {remote_loc_pet}predictions.csv', f'> {hash(session_id)}/output/predictions.csv']
                outs, errs = bash_cmd(scp_cmd, session_id, shell=True)
                print(outs, errs)
                return {"status": "finished"}
            else:
                with open(f'{hash(session_id)}/logging.txt', 'a') as file:
                    file.write('Training Complete\n')
                ssh_cmd = ['sshpass', '-e', 'ssh',
                           f'{user}@{cluster_name}', f'cd {remote_loc_pet} '
                                                     f'&& find . -name "results.json" -type f']
                outs, errs = bash_cmd(ssh_cmd, session_id)
                print(outs, errs)
                files = outs.decode("utf-8")
                for f in files.rstrip().split("\n"):
                    f = f.lstrip("./")
                    os.makedirs(f"{hash(session_id)}/{f.rstrip('results.json')}", exist_ok=True)
                    while not os.path.exists(f"{hash(session_id)}/{f.rstrip('results.json')}"):
                        time.sleep(1)
                    scp_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                               f'cat {remote_loc_pet}{f} > {hash(session_id)}/{f}']
                    outs, errs = bash_cmd(scp_cmd, session_id, shell=True)
                    print(outs, errs)
                '''Call Results'''
                results(session_id)
                return {"Pet": "finished"}
        elif status == "F":
            raise Exception("Job could not finish. Please login and try again")

        time.sleep(5)

        ssh_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                   f'cat /home/{user}/{log_file.split("/")[-1]}']
        outs, errs = bash_cmd(ssh_cmd, session_id)
        log_contents = outs.decode('utf-8')

        # Update the log file on the local machine
        with open(f"{log_file}", 'w') as f:
            f.write(log_contents)


def results(session_id: UUID = Depends(sessionObj.get_session_id)):
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
        

@app.post("/extract-file", dependencies=[Depends(sessionObj.get_session_id)])
async def extract_file(file: UploadFile = File(...), session_id: UUID = Depends(sessionObj.get_session_id)):
    file_upload = tarfile.open(fileobj=file.file, mode="r:gz")
    file_upload.extractall(f'{hash(session_id)}/data_uploaded')

    # Read the train and test data into dataframes
    columns = ["label", "text"]
    train_df = pd.read_csv(f'{hash(session_id)}/data_uploaded/yelp_review_polarity_csv/train.csv', names=columns)
    test_df = pd.read_csv(f'{hash(session_id)}/data_uploaded/yelp_review_polarity_csv/test.csv', names=columns)

    # Plot the distribution of labels for train and test data separately
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(7, 5))
    ax1.bar(train_df["label"].unique(), train_df["label"].value_counts(), width=0.5)
    ax1.set_title("Train Label Distribution")
    ax1.set_xlabel("Label")
    ax1.set_ylabel("Count")
    ax2.bar(test_df["label"].unique(), test_df["label"].value_counts(), width=0.5)
    ax2.set_title("Test Label Distribution")
    ax2.set_xlabel("Label")
    ax2.set_ylabel("Count")

    # Add text information about the label distribution to the chart
    train_label_counts = train_df["label"].value_counts()
    test_label_counts = test_df["label"].value_counts()

    ax1.set_xticks(train_df["label"].unique())
    ax2.set_xticks(test_df["label"].unique())

    max_y = max(train_df["label"].value_counts().max(), test_df["label"].value_counts().max())
    ax1.set_ylim([0, max_y])
    ax2.set_ylim([0, max_y])

    # Save the chart to a file
    plt.savefig("static/chart.png", dpi=100)

    return {"message": "File extracted successfully."}


