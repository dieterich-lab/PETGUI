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
import random
from uuid import UUID, uuid4



from app.controller import templating
from app.dto.session import SessionData, UUID
from .services.session import SessionService
from .services.ldap import LdapService



'''START APP'''
app = FastAPI()
'''Include routers'''
app.include_router(templating.router)
app.mount("/static", StaticFiles(directory="static"), name="static")
local = False # If running app locally
ssh = "sshpass"
if local:
    ssh = "/opt/homebrew/bin/sshpass"

    
class User:
    session: SessionService
    ldap: LdapService


app.state = User()


def get_session_service(request: Request):
    return request.app.state.session

@app.get("/", name="start")
def main():
    return RedirectResponse(url="/login")

@app.get("/get_cookie")
def get(request: Request, session: SessionService=Depends(get_session_service)):
    cookies = request.cookies
    session = get_session_service(request)
    print(cookies, session)
    return {"sess": session, "cook": cookies}

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not LdapService.authenticate_ldap(username=username, password=password):
        error = 'Invalid username or password'
        return await templating.login_form(request, error)
    response = RedirectResponse(url=request.url_for("homepage"), status_code=303)
    session = await create_session(request, username, response)
    session_uuid = session.get_session_id()
    print(session_uuid, hash(session_uuid))
    os.environ[f"{hash(session_uuid)}"] = password
    os.makedirs(f"./{hash(session_uuid)}", exist_ok=True)  # If run with new conf.
    return response

@app.get("/whoami", name="whoami")
def whoami(session: SessionService = Depends(get_session_service)):
    try:
        return session
    except AttributeError as e:
        print(str(e))


async def create_session(request: Request, user: str, response: Response):
    session_id = uuid4()
    remote_loc = f"/home/{user}/{hash(session_id)}/"
    remote_loc_pet = f"/home/{user}/{hash(session_id)}/pet/"
    cluster_name = "cluster.dieterichlab.org"
    log_file = f"{hash(session_id)}/logging.txt"
    last_pos_file = f"{hash(session_id)}/last_pos.txt"
    data = SessionData(username=user, remote_loc=remote_loc, remote_loc_pet=remote_loc_pet, cluster_name=cluster_name,
                       log_file=log_file, last_pos_file=last_pos_file)
    request.app.state.session = SessionService(data, session_id)
    session = request.app.state.session
    session.create_cookie(response=response)
    await session.create_backend()
    return session


@app.get("/steps", name="steps")
def get_steps(session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()
    with open(f"./{hash(session_id)}/data.json") as f:
        data = json.load(f)
    count_tmp = len([tmp for tmp in data.keys() if "template_" in tmp])
    count_steps = 18 + (count_tmp-1) * 5
    return {"steps": count_steps}


@app.get("/logging/start_train")
async def run(session: SessionService = Depends(get_session_service)):
    """
    Kicks off PET by calling train method.
    """
    '''Start PET'''
    print("Training starting..")
    job_id = await submit_job(session, False)
    t = threading.Thread(target=check_job_status, args=(session, job_id, False))
    t.start()


@app.get("/final/start_prediction")
async def label_prediction(request: Request, session: SessionService = Depends(get_session_service)):
    '''Start Predicttion'''
    try:
        print("Prediction starting..")
        job_id = await submit_job(session, True)
        return check_job_status(session, job_id, True)
    except Exception as e:
        error = "Something went wrong, please reload the page and try again"
        return await templating.get_final_template(request, error)


async def submit_job(session: SessionService = Depends(get_session_service), predict: bool = False):
    # Copy the SLURM script file to the remote cluster
    print("Submitting job..")

    user = session.session_data.username
    remote_loc = session.session_data.remote_loc
    remote_loc_pet = session.session_data.remote_loc_pet
    cluster_name = session.session_data.cluster_name
    session_id = session.get_session_id()

    if predict:

        try:
            scp_cmd = ["sshpass", '-e', 'scp', '-r', f'{str(hash(session_id))}/data_uploaded/unlabeled',
                       f'{user}@{cluster_name}:{remote_loc_pet}data_uploaded/']
            outs, errs = bash_cmd(session, scp_cmd)
            ssh_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                       f'sbatch {remote_loc_pet}predict.sh {remote_loc.split("/")[-2]}']
            outs, errs = bash_cmd(session, ssh_cmd)
            print("Prediction: ", outs)
            # Get the job ID from the output of the sbatch command
            job_id = outs.decode('utf-8').strip().split()[-1]
            return job_id
        except Exception as e:
            raise e

    else:
        mkdir_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}', f'mkdir {remote_loc}']
        outs, errs = bash_cmd(session, mkdir_cmd)
        dir = hash(session_id)

        files = ["pet", "data.json", "train.sh", "data_uploaded", "predict.sh"]
        files = [str(dir) + "/" + f if f == "data.json" or f == "data_uploaded" else f for f in files]
        print(files)
        for f in files:
            scp_cmd = ["sshpass", '-e', 'scp', '-r', f,
                   f'{user}@{cluster_name}:{remote_loc}' if "pet" in f
                   else f'{user}@{cluster_name}:{remote_loc_pet}']
            outs, errs = bash_cmd(session, scp_cmd)
            print(outs, errs)

        # Submit the SLURM job via SSH
        ssh_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                   f'sbatch {remote_loc_pet}train.sh {remote_loc.split("/")[-2]}']
        outs, errs = bash_cmd(session, ssh_cmd)
        # Get the job ID from the output of the sbatch command
        job_id = outs.decode('utf-8').strip().split()[-1]
        return job_id


def bash_cmd(session: SessionService = Depends(get_session_service), cmd=None, shell: bool = False):
    session_id = session.get_session_id()
    proc = subprocess.Popen(" ".join(cmd) if shell else cmd, env={"SSHPASS": os.environ[f"{hash(session_id)}"]}, shell=shell,
                            stdout=subprocess.PIPE, stderr=PIPE)
    outs, errs = proc.communicate()
    return outs, errs


def check_job_status(session: SessionService = Depends(get_session_service), job_id: str = None, predict: bool = False):
    user = session.session_data.username
    remote_loc_pet = session.session_data.remote_loc_pet
    cluster_name = session.session_data.cluster_name
    log_file = session.session_data.log_file
    session_id = session.get_session_id()
    while True:
        cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}', f"squeue -j {job_id} -h -t all | awk '{{print $5}}'"]
        outs, errs = bash_cmd(session, cmd)
        status = outs.decode("utf-8").strip().split()[-1]
        print(status, outs, errs)
        if status == "R":
            pass
        elif status == "CD":
            if predict:
                scp_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                           f'cat {remote_loc_pet}predictions.csv', f'> {hash(session_id)}/output/predictions.csv']
                outs, errs = bash_cmd(session, scp_cmd, shell=True)
                print(outs, errs)
                return {"status": "finished"}
            else:
                with open(f'{hash(session_id)}/logging.txt', 'a') as file:
                    file.write('Training Complete\n')
                ssh_cmd = ["sshpass", '-e', 'ssh',
                           f'{user}@{cluster_name}', f'cd {remote_loc_pet} '
                                                     f'&& find . -name "results.json" -type f']
                outs, errs = bash_cmd(session, ssh_cmd)
                print(outs, errs)
                files = outs.decode("utf-8")
                for f in files.rstrip().split("\n"):
                    f = f.lstrip("./")
                    os.makedirs(f"{hash(session_id)}/{f.rstrip('results.json')}", exist_ok=True)
                    while not os.path.exists(f"{hash(session_id)}/{f.rstrip('results.json')}"):
                        time.sleep(1)
                    scp_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                               f'cat {remote_loc_pet}{f} > {hash(session_id)}/{f}']
                    outs, errs = bash_cmd(session, scp_cmd, shell=True)
                    print(outs, errs)
                '''Call Results'''
                results(session)
                return {"Pet": "finished"}
        elif status == "F":
            raise Exception("Job could not finish. Please login and try again")

        time.sleep(5)

        ssh_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                   f'cat /home/{user}/{log_file.split("/")[-1]}']
        outs, errs = bash_cmd(session, ssh_cmd)
        log_contents = outs.decode('utf-8')

        # Update the log file on the local machine
        with open(f"{log_file}", 'w') as f:
            f.write(log_contents)


def results(session: SessionService = Depends(get_session_service)):
    """
    Saves results.json for each pattern-iteration pair of output/final directory in a dictionary.
    Returns:
        html page with results & homepage redirection buttons
    """
    session_id = session.get_session_id()
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
            k = f"Pattern-{int(d[1]) + 1} Iteration 1"
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
            # scores[k]["pre-rec-f1-supp"] = [round(float(scr), 2) for l in scores.values() for scr in l]

    with open(f"{hash(session_id)}/results.json", "w") as res:
        json.dump(scores, res)


@app.post("/extract-file")
async def extract_file(file: UploadFile = File(...), session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()
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


@app.post("/label-distribution")
async def label_distribution(session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()
    # Read the prediction data into a dataframe
    df = pd.read_csv(f'{hash(session_id)}/output/predictions.csv')

    # Create a bar chart of the label distribution
    label_counts = df['label'].value_counts()
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(211)
    label_counts.plot(kind='bar', width=0.3, ax=ax)
    ax.set_title('Label Counts')
    ax.set_xlabel('Label')
    ax.set_ylabel('Number of Examples')
    random_examples = df.sample(n=5)

    # Format the text column to show only the first 25 tokens
    random_examples['text'] = random_examples['text'].apply(
        lambda x: ' '.join(x.split()[:10]) + ('...' if len(x.split()) > 10 else ''))

    # Create a table to display the randomly selected examples
    table_data = [['Label', 'Text']]
    for _, row in random_examples.iterrows():
        table_data.append([row['label'], row['text']])

    table = ax.table(cellText=table_data, loc='bottom', cellLoc='left', bbox=[0, -0.8, 1, 0.5])

    table.auto_set_column_width(col=list(range(2)))
    # Create a string with the label and text for each example


    # Save the chart to a file
    plt.savefig("static/chart_prediction.png", dpi=100)

    return {"message": "Label distribution chart created successfully."}

