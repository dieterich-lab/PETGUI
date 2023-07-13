import glob
import pathlib
import concurrent.futures
from fastapi import FastAPI, Depends, UploadFile, File, Request, Response, Form
from fastapi.templating import Jinja2Templates
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
import csv
import numpy as np

import shutil

from app.controller import templating
from app.controller import session
from .services.session import SessionService




'''START APP'''
app = FastAPI()
'''Include routers'''
app.include_router(templating.router)
app.include_router(session.session_router)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
local = False # If running app locally
ssh = "sshpass"
if local:
    ssh = "/opt/homebrew/bin/sshpass"



class User:
    session: SessionService
    job_id: str = None
    job_status: str
    event: threading.Event = None


app.state = User()


def get_session_service(request: Request):
    return request.app.state.session

@app.get("/", name="start")
def main():
    return RedirectResponse(url="/start")

@app.get("/get_cookie")
def get(request: Request, session: SessionService = Depends(get_session_service)):
    cookies = request.cookies
    session = get_session_service(request)
    print(cookies, session)
    return {"sess": session, "cook": cookies}


@app.get("/whoami", name="whoami")
def whoami(session: SessionService = Depends(get_session_service)):
    try:
        return session
    except AttributeError as e:
        print(str(e))


@app.get("/steps", name="steps")
def get_steps(session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()
    with open(f"./{hash(session_id)}/data.json") as f:
        data = json.load(f)
    count_tmp = len([tmp for tmp in data.keys() if "template_" in tmp])
    count_steps = 18 + (count_tmp-1) * 5
    return {"steps": count_steps}


@app.get("/logging/start_train")
async def run(request: Request, session: SessionService = Depends(get_session_service)):
    """
    Kicks off PET by calling train method.
    """
    '''Start PET'''
    print("Training starting..")
    try:
        request.app.state.job_id = await submit_job(session, False)
        request.app.state.event = threading.Event()
        t = threading.Thread(target=check_job_status, args=(request, session, request.app.state.job_id, False))
        t.start()
    except Exception as e:
        return templating.logging(request, str(e))



@app.get("/abort_job")
async def run(request: Request, session: SessionService = Depends(get_session_service), final: bool = False):
    """
    Aborts current job.
    """
    try:
        request.app.state.job_status = None
        user = session.session_data.username
        cluster_name = session.session_data.cluster_name
        job_id = request.app.state.job_id
        print(f"Aborting job with id: {job_id}")
        ssh_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                   f'scancel {job_id}']
        outs, errs = bash_cmd(session, ssh_cmd, shell=True)
        print(outs, errs)
    except Exception as e:
        print(str(e))
        pass
    if final:
        return
    else:
        return RedirectResponse(request.url_for("clean"), status_code=303)



@app.get("/final/start_prediction")
async def label_prediction(request: Request, session: SessionService = Depends(get_session_service), check: bool = False):
    '''Start Predicttion'''
    if check:
        try:
            if request.app.state.job_status == "CD":
                return {"status": "CD"}
        except:
            pass
    else:
        try:
            print("Prediction starting..")
            request.app.state.job_id = await submit_job(session, True)
            request.app.state.event = threading.Event()
            t = threading.Thread(target = check_job_status, args = (request, session, request.app.state.job_id, True))
            t.start()
        except Exception as e:
            error = "Something went wrong, please reload the page and try again"
            return templating.get_final_template(request, error)


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
        print(job_id)
        return job_id


def bash_cmd(session: SessionService = Depends(get_session_service), cmd=None, shell: bool = False):
    session_id = session.get_session_id()
    proc = subprocess.Popen(" ".join(cmd) if shell else cmd, env={"SSHPASS": os.environ[f"{hash(session_id)}"]}, shell=shell,
                            stdout=subprocess.PIPE, stderr=PIPE)
    outs, errs = proc.communicate()
    return outs, errs


def check_job_status(request: Request, session: SessionService = Depends(get_session_service), job_id: str = None, predict: bool = False):
    user = session.session_data.username
    remote_loc_pet = session.session_data.remote_loc_pet
    cluster_name = session.session_data.cluster_name
    log_file = session.session_data.log_file
    session_id = session.get_session_id()
    while request.app.state.event:
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
                request.app.state.job_status = "CD"
                return {"Prediction": "finished"}
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
                return {"Training": "finished"}
        elif status == "CA":
            return
        elif status == "F":
            raise Exception("Job could not finish. Please make sure your parameters are correct.")


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

def detect_delimiter(filename):
    try:
        df = pd.read_csv(filename, nrows=1)  # 读取文件的第一行数据
        if '\t' in df.columns[0]:
            return '\t'
        else:
            return ','
    except pd.errors.ParserError:
        raise Exception

@app.post("/extract-file")
async def extract_file(request: Request, file: UploadFile = File(...), session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()
    upload_folder = f"{hash(session_id)}/data_uploaded/"

    if os.path.exists(upload_folder):
        shutil.rmtree(upload_folder)
    os.makedirs(upload_folder)
    try:
        file_upload = tarfile.open(fileobj=file.file, mode="r:gz", errors="ignore")
        file_upload.extractall(f'{hash(session_id)}/data_uploaded')
    except:
        return templates.TemplateResponse('index.html', {'request': request,
                                                             'error': "Invalid File Type: Please upload your data as a zip file with the extension '.tar.gz'"})
    # Print the extracted file names
    extracted_files = [member.name for member in file_upload.getmembers()]
    print("Extracted files:", extracted_files)

    # Identify the extracted folder
    extracted_folder = None
    for root, dirs, files in os.walk(f'{hash(session_id)}/data_uploaded'):
        if len(dirs) == 1:  # Assuming only one subdirectory within the extracted files
            extracted_folder = dirs[0]
            break
        elif len(dirs) == 0:
            extracted_folder = pathlib.Path(f'{hash(session_id)}/data_uploaded/{file.filename.split(".")[0]}')
            extracted_folder.mkdir(parents=True, exist_ok=True)
            for f in files:
                try:
                    shutil.move(f'{hash(session_id)}/data_uploaded/{f}', extracted_folder)
                except FileNotFoundError as e:
                    print(os.curdir, str(e))
        if "unlabeled.csv" in files:
            os.environ[f"{hash(session_id)}_unlabeled"] = "True"

    print("Extracted folder:", extracted_folder)

    # Read the train and test data into dataframes
    # Read the train and test data into dataframes
    columns = ["label", "text"]

    filename = "".join(glob.glob(f'{hash(session_id)}/data_uploaded/*/train.csv'))
    delimiter = detect_delimiter(filename)
    os.environ[f"{hash(session_id)}_delimiter"] = delimiter
    print(delimiter)

    train_df = pd.read_csv("".join(glob.glob(f'{hash(session_id)}/data_uploaded/*/train.csv')), sep=delimiter,
                           names=columns)
    test_df = pd.read_csv("".join(glob.glob(f'{hash(session_id)}/data_uploaded/*/test.csv')), sep=delimiter,
                          names=columns)

    # Plot the distribution of labels for train and test data separately


    # Add text information about the label distribution to the chart
    train_label_counts = train_df["label"].value_counts()
    test_label_counts = test_df["label"].value_counts()

    first_label = train_df.at[0,"label"]
    print(first_label)
    # print(type(first_label))
    is_numeric_label = isinstance(first_label, int) or len(str(first_label)) == 1
    #print(train_df["label"].unique())

    unique_labels = train_df["label"].unique()

    label_dict = {index:str(label) for index, label in enumerate(unique_labels)}

    json_file_path = f'{hash(session_id)}/label_dict.json'
    with open(json_file_path, "w") as json_file:
        json.dump(label_dict, json_file)

    print(is_numeric_label)

    if not is_numeric_label:
        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(7, 12))  # Increase the figure height

        # Sort labels and counts for train data
        train_labels, train_counts = zip(
            *sorted(zip(train_df["label"].unique(), train_df["label"].value_counts()), key=lambda x: x[1]))
        ax1.barh(np.arange(len(train_labels)), train_counts, height=0.5)
        ax1.set_title("Train Label Distribution")
        ax1.set_xlabel("Count")
        ax1.set_ylabel("Label")
        ax1.set_yticks(np.arange(len(train_labels)))
        ax1.set_yticklabels(train_labels, rotation=0)  # Rotate the y-axis tick labels if necessary

        # Sort labels and counts for test data
        test_labels, test_counts = zip(
            *sorted(zip(test_df["label"].unique(), test_df["label"].value_counts()), key=lambda x: x[1]))
        ax2.barh(np.arange(len(test_labels)), test_counts, height=0.5)
        ax2.set_title("Test Label Distribution")
        ax2.set_xlabel("Count")
        ax2.set_ylabel("Label")
        ax2.set_yticks(np.arange(len(test_labels)))
        ax2.set_yticklabels(test_labels, rotation=0)
        max_y = max(train_df["label"].value_counts().max(), test_df["label"].value_counts().max())
        ax1.set_ylim(-0.5, len(train_labels) - 0.5)
        ax2.set_ylim(-0.5, len(test_labels) - 0.5)
    else:
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(7, 5))
        ax1.bar(train_df["label"].unique(), train_df["label"].value_counts(), width=0.5)
        ax1.set_title("Train Label Distribution")
        ax1.set_xlabel("Label")
        ax1.set_ylabel("Count")
        ax2.bar(test_df["label"].unique(), test_df["label"].value_counts(), width=0.5)
        ax2.set_title("Test Label Distribution")
        ax2.set_xlabel("Label")
        ax2.set_ylabel("Count")
        ax1.set_xticks(train_df["label"].unique())
        ax2.set_xticks(test_df["label"].unique())
        max_y = max(train_df["label"].value_counts().max(), test_df["label"].value_counts().max())
        ax1.set_ylim([0, max_y])
        ax2.set_ylim([0, max_y])


    # Save the chart to a file
    plt.savefig("static/chart.png", dpi=100)

    print("message", "File extracted successfully.")


@app.get("/report-labels")
def report(session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()
    columns = ["label", "text"]

    filename = "".join(glob.glob(f'{hash(session_id)}/data_uploaded/*/train.csv'))
    delimiter = detect_delimiter(filename)
    train_df = pd.read_csv("".join(glob.glob(f'{hash(session_id)}/data_uploaded/*/train.csv')), sep=delimiter,
                               names=columns)
    labels = set(str(i) for i in train_df.label)
    print(labels)

    return {"list": labels}


@app.post("/label-distribution")
async def label_distribution(session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()
    # Read the prediction data into a dataframe
    df = pd.read_csv(f'{hash(session_id)}/output/predictions.csv')

    with open(f'{hash(session_id)}/label_dict.json', 'r') as file:
        label_mapping = json.load(file)

    df['label'] = df['label'].astype(str).map(label_mapping)

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


@app.post("/label-change")
async def label_change (session: SessionService = Depends(get_session_service)):
    session_id = session.get_session_id()

    with open(f'{hash(session_id)}/label_dict.json', 'r') as file:
        label_mapping = json.load(file)


    with open(f'{hash(session_id)}/results.json', 'r') as file:
        json_data = json.load(file)

    for key in json_data:
        for i in range(len(json_data[key]["pre-rec-f1-supp"])):
            label_number = json_data[key]["pre-rec-f1-supp"][i].split(':')[1].split()[0]
            if label_number in label_mapping:
                json_data[key]["pre-rec-f1-supp"][i] = json_data[key]["pre-rec-f1-supp"][i].replace(
                    "Label: {}".format(label_number),
                    "Label: {}".format(label_mapping[label_number]))
    with open(f'{hash(session_id)}/results.json', 'w') as file:
        json.dump(json_data, file, ensure_ascii=False)

