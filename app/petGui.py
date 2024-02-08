import asyncio
import glob
import pathlib
from uuid import UUID
from fastapi import FastAPI, Depends, UploadFile, File, Request
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
import numpy as np
import shutil
from app.controller import templating as templating_controller
from app.controller import session as session_controller
from .dto.session import backend
from .services.session import set_event, set_job_status


'''START APP'''
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
local = False  # If running app locally
ssh = "sshpass"
if local:
    ssh = "/opt/homebrew/bin/sshpass"


async def get_session(request: Request):
    try:
        session = await backend.read(UUID(request.cookies["session"]))
    except KeyError:
        return None
    return session

'''Include routers'''
app.include_router(templating_controller.router, dependencies=[Depends(get_session)])
app.include_router(session_controller.session_router, dependencies=[Depends(get_session)])


@app.get("/", name="start")
def main():
    return RedirectResponse(url="/start", status_code=303)


@app.get("/whoami", name="whoami")
async def whoami(session=Depends(get_session)):
    return session


@app.get("/steps", name="steps")
def get_steps(session=Depends(get_session)):
    session_id = hash(session.id)
    with open(f"./{(session_id)}/data.json") as f:
        data = json.load(f)
    count_tmp = len([tmp for tmp in data.keys() if "template_" in tmp])
    count_steps = 18 + (count_tmp-1) * 5
    return {"steps": count_steps}


@app.get("/logging/start_train", name="start_train")
async def run(request: Request, session=Depends(get_session)):
    """
    Kicks off PET by calling train method.
    """
    '''Start PET'''
    try:
        session_id = hash(session.id)
        session.job_id = await submit_job(session, False)
        await set_event(session.id, session, event=False)
        # Check if event is set
        t = threading.Thread(target=check_job, args=(session, session.job_id, False))
        t.start()
        print("Training started")
    except Exception as e:
        print(str(e))
        return templating_controller.logging(request, str(e))


def check_job(session, job_id, predict):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(check_job_status(session, job_id, predict))
    loop.close()


@app.get("/abort_job")
async def abort(session=Depends(get_session), final: bool = False):
    session_id = hash(session.id)
    """
    Aborts current job.
    """
    try:
        user = session.username
        cluster_name = session.cluster_name
        job_id = session.job_id
        print(f"Aborting job with id: {job_id}")
        ssh_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                   f'scancel {job_id}']
        outs, errs = bash_cmd(session_id, ssh_cmd, shell=True)
        print(outs, errs)
    except Exception as e:
        print(str(e))
        pass
    if final:
        return
    else:
        return await templating_controller.clean(session, False)


@app.get("/final/start_prediction")
async def label_prediction(request: Request, session=Depends(get_session),
                           check: bool = False):
    session_id = hash(session.id)
    # Start Prediction
    if check:
        try:
            return {"status": session.job_status}
        except KeyError:
            pass
    else:
        try:
            session.job_id = await submit_job(session, True)
            await set_event(session.id, session, event=False)
            # Check if event is set
            t = threading.Thread(target=check_job, args=(session, session.job_id, True))
            t.start()
            return {"Prediction": "started"}
        except Exception as e:
            print(str(e))
            return templating_controller.logging(request, str(e))


@app.get("submit_job")
async def submit_job(session=Depends(get_session), predict: bool = False):
    # Copy the SLURM script file to the remote cluster
    print("Submitting job..")

    user = session.username
    remote_loc = session.remote_loc
    remote_loc_pet = session.remote_loc_pet
    cluster_name = session.cluster_name
    session_id = hash(session.id)

    if predict:
        try:
            scp_cmd = ["sshpass", '-e', 'scp', '-r', f'{session_id}/data_uploaded/unlabeled',
                       f'{user}@{cluster_name}:{remote_loc_pet}data_uploaded/']
            outs, errs = bash_cmd(session_id, scp_cmd)
            print(outs, errs)
            ssh_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                       f'sbatch {remote_loc_pet}predict.sh {remote_loc.split("/")[-2]}']
            outs, errs = bash_cmd(session_id, ssh_cmd)
            print("Prediction: ", outs)
            # Get the job ID from the output of the sbatch command
            job_id = outs.decode('utf-8').strip().split()[-1]
            return job_id
        except Exception as e:
            raise e

    else:
        mkdir_cmd = ["sshpass", '-e', 'ssh', '-o', 'StrictHostKeyChecking=no', f'{user}@{cluster_name}', f'mkdir {remote_loc}']
        outs, errs = bash_cmd(session_id, mkdir_cmd)
        print(outs, errs)
        await create_venv(session_id, user, cluster_name, remote_loc)
        files = ["pet", "data.json", "conf/train.sh", "data_uploaded", "conf/predict.sh", "requirements.txt"]
        files = [str(session_id) + "/" + f if f == "data.json" or f == "data_uploaded" else f for f in files]
        print(files)
        for f in files:
            scp_cmd = ["sshpass", '-e', 'scp', '-r', f,
                       f'{user}@{cluster_name}:{remote_loc}' if "pet" in f
                       else f'{user}@{cluster_name}:{remote_loc_pet}']
            outs, errs = bash_cmd(session_id, scp_cmd)
            print("Found here:", outs, errs)

        # Submit the SLURM job via SSH
        ssh_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                   f'sbatch {remote_loc_pet}train.sh {remote_loc.split("/")[-2]}']
        outs, errs = bash_cmd(session_id, ssh_cmd)
        # Get the job ID from the output of the sbatch command
        job_id = outs.decode('utf-8').strip().split()[-1]
        print(job_id)
        return job_id


async def create_venv(session_id, user, cluster_name, remote_loc):
    env_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}', f'python3.11 -m venv {remote_loc}/petgui']
    outs, errs = bash_cmd(session_id, env_cmd)
    print(outs, errs)
    # act_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}', f'source petgui/bin/activate']
    # outs, errs = bash_cmd(session_id, act_cmd)
    # print(outs, errs)
    # pip_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}', f'pip install {remote_loc}/requirements.txt']
    # outs, errs = bash_cmd(session_id, pip_cmd)
    # print(outs, errs)


def bash_cmd(session_id: int, cmd=None, shell: bool = False):
    proc = subprocess.Popen(" ".join(cmd) if shell else cmd, env={"SSHPASS": os.environ[f"{session_id}"]}, shell=shell,
                            stdout=subprocess.PIPE, stderr=PIPE)
    outs, errs = proc.communicate()
    return outs, errs


@app.get("check_job_status", name="check_job_status")
async def check_job_status(session=Depends(get_session), job_id: str = None, predict: bool = False):
    global status
    user = session.username
    remote_loc_pet = session.remote_loc_pet
    cluster_name = session.cluster_name
    log_file = session.log_file
    session_id = hash(session.id)
    event = session.event
    await set_event(session.id, session, event=False)
    print(event)
    while not event:
        print(event)
        cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}', f"squeue -j {job_id} -h -t all | awk '{{print $5}}'"]
        outs, errs = bash_cmd(session_id, cmd)
        try:
            status = outs.decode("utf-8").strip().split()[-1]
            print(status, outs, errs)
        except IndexError:
            pass
        if status == "R":
            await set_job_status(session.id, session, job_status="R", event=False)
            pass
        elif status == "CD":
            await set_job_status(session.id, session, job_status="CD", event=False)
            if predict:
                scp_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                           f'cat {remote_loc_pet}predictions.csv', f'> {(session_id)}/output/predictions.csv']
                outs, errs = bash_cmd(session_id, scp_cmd, shell=True)
                print(outs, errs)
                return {"Prediction": "finished"}
            else:
                with open(log_file, 'a') as file:
                    file.write('Training Complete\n')
                ssh_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}', f'cd {remote_loc_pet}'
                                                   f'&& find . -name "results.json" -type f']
                outs, errs = bash_cmd(session_id, ssh_cmd, )
                print(outs, errs)
                files = outs.decode("utf-8")
                for f in files.rstrip().split("\n"):
                    f = f.lstrip("./")
                    os.makedirs(f"{session_id}/{f.rstrip('results.json')}", exist_ok=True)
                    while not os.path.exists(f"{session_id}/{f.rstrip('results.json')}"):
                        time.sleep(1)
                    scp_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                               f'cat {remote_loc_pet}{f} > {session_id}/{f}']
                    outs, errs = bash_cmd(session_id, scp_cmd, shell=True)
                    print(outs, errs)
                '''Call Results'''
                results(str(session_id))
                return {"Training": "finished"}
        elif status == "CA":
            await set_job_status(session.id, session, job_status="CA", event=False)
            return
        elif status == "F":
            await set_job_status(session.id, session, job_status="F", event=False)
            raise Exception("Job could not finish. Please make sure your parameters are correct.")

        time.sleep(5)

        ssh_cmd = ["sshpass", '-e', 'ssh', f'{user}@{cluster_name}',
                   f'cat /home/{user}/{log_file.split("/")[-1]}']
        outs, errs = bash_cmd(session_id, ssh_cmd)
        log_contents = outs.decode('utf-8')

        # Update the log file on the local machine
        with open(log_file, 'w') as f:
            f.write(log_contents)


def results(session_id: str):
    """
    Saves results.json for each pattern-iteration pair of output/final directory in a dictionary.
    Returns:
        html page with results & homepage redirection buttons
    """
    print(session_id)
    dirs = next(os.walk(f"{session_id}/output/"))[1]
    scores = {}
    for d in dirs:
        final = ""
        if "final" in d:
            k = "Final"
            scores[k] = {"acc": "-", "pre-rec-f1-supp": []}
            finals = next(os.walk(f"{session_id}/output/final/"))[1]
            assert len(finals) == 1
            final += f"/{finals[0]}"
        else:
            k = f"Pattern-{int(d[1]) + 1} Iteration 1"
            scores[k] = {"acc": "-", "pre-rec-f1-supp": []}
            final = ""
        with open(f"{session_id}/output/{d}{final}/results.json") as f:
            json_scores = json.load(f)
            acc = round(json_scores["test_set_after_training"]["acc"], 2)
            pre, rec, f1, supp = json_scores["test_set_after_training"]["pre-rec-f1-supp"]
            labels = [i for i in range(len(pre))]
            for l in labels:
                scores[k]["pre-rec-f1-supp"].append(f"Label: {l} Pre: {round(pre[l], 2)}, Rec: {round(rec[l], 2)},"
                                                    f"F1: {round(f1[l], 2)}, Supp: {supp[0]}")
            scores[k]["acc"] = acc
            # scores[k]["pre-rec-f1-supp"] = [round(float(scr), 2) for l in scores.values() for scr in l]
    with open(f"{session_id}/results.json", "w") as res:
        json.dump(scores, res)
    return


@app.post("/label-change")
async def label_change(session=Depends(get_session)):
    session_id = hash(session.id)
    with open(f'{(session_id)}/label_dict.json', 'r') as file:
        label_mapping = json.load(file)

    with open(f'{(session_id)}/results.json', 'r') as file:
        json_data = json.load(file)

    for key in json_data:
        for i in range(len(json_data[key]["pre-rec-f1-supp"])):
            label_number = json_data[key]["pre-rec-f1-supp"][i].split(':')[1].split()[0]
            if label_number in label_mapping:
                json_data[key]["pre-rec-f1-supp"][i] = json_data[key]["pre-rec-f1-supp"][i].replace(
                    "Label: {}".format(label_number),
                    "Label: {}".format(label_mapping[label_number]))
    with open(f'{(session_id)}/results.json', 'w') as file:
        json.dump(json_data, file, ensure_ascii=False)


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
async def extract_file(request: Request, file: UploadFile = File(...), session=Depends(get_session)):
    session_id = hash(session.id)
    upload_folder = f"{session_id}/data_uploaded/"

    if os.path.exists(upload_folder):
        shutil.rmtree(upload_folder)
    os.makedirs(upload_folder)
    try:
        file_upload = tarfile.open(fileobj=file.file, mode="r:gz", errors="ignore")
        file_upload.extractall(f'{(session_id)}/data_uploaded')
    except:
        return templates.TemplateResponse('index.html', {'request': request,
                                                         'error': "Invalid File Type: Please upload your data"
                                                                  " as a zip file with the extension '.tar.gz'"})
    # Print the extracted file names
    extracted_files = [member.name for member in file_upload.getmembers()]
    print("Extracted files:", extracted_files)

    # Identify the extracted folder
    extracted_folder = None
    for root, dirs, files in os.walk(f'{(session_id)}/data_uploaded'):
        if len(dirs) == 1:  # Assuming only one subdirectory within the extracted files
            extracted_folder = dirs[0]
            break
        elif len(dirs) == 0:
            extracted_folder = pathlib.Path(f'{(session_id)}/data_uploaded/{file.filename.split(".")[0]}')
            extracted_folder.mkdir(parents=True, exist_ok=True)
            for f in files:
                try:
                    shutil.move(f'{(session_id)}/data_uploaded/{f}', extracted_folder)
                except FileNotFoundError as e:
                    print(os.curdir, str(e))
        if "unlabeled.csv" in files:
            os.environ[f"{(session_id)}_unlabeled"] = "True"

    print("Extracted folder:", extracted_folder)

    # Read the train and test data into dataframes
    # Read the train and test data into dataframes
    columns = ["label", "text"]

    filename = "".join(glob.glob(f'{(session_id)}/data_uploaded/*/train.csv'))
    delimiter = detect_delimiter(filename)
    os.environ[f"{(session_id)}_delimiter"] = delimiter
    print(delimiter)

    train_df = pd.read_csv("".join(glob.glob(f'{(session_id)}/data_uploaded/*/train.csv')), sep=delimiter,
                           names=columns)
    test_df = pd.read_csv("".join(glob.glob(f'{(session_id)}/data_uploaded/*/test.csv')), sep=delimiter,
                          names=columns)

    # Plot the distribution of labels for train and test data separately

    # Add text information about the label distribution to the chart
    train_label_counts = train_df["label"].value_counts()
    test_label_counts = test_df["label"].value_counts()

    first_label = train_df.at[0, "label"]
    print(first_label)
    # print(type(first_label))
    is_numeric_label = isinstance(first_label, int) or len(str(first_label)) == 1
    # print(train_df["label"].unique())

    unique_labels = train_df["label"].unique()

    label_dict = {index: str(label) for index, label in enumerate(unique_labels)}

    json_file_path = f'{(session_id)}/label_dict.json'
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

    return{"message": "File extracted successfully."}


@app.get("/report-labels")
def report(session=Depends(get_session)):
    session_id = hash(session.id)
    columns = ["label", "text"]

    filename = "".join(glob.glob(f'{(session_id)}/data_uploaded/*/train.csv'))
    delimiter = detect_delimiter(filename)
    train_df = pd.read_csv("".join(glob.glob(f'{(session_id)}/data_uploaded/*/train.csv')), sep=delimiter,
                           names=columns)
    labels = set(str(i) for i in train_df.label)
    print("labels: ", labels)
    return {"list": labels}


@app.post("/label-distribution")
async def label_distribution(session=Depends(get_session)):
    # Read the prediction data into a dataframe
    session_id = hash(session.id)
    df = pd.read_csv(f'{(session_id)}/output/predictions.csv')

    # Shorten the label to the first 10 characters
    df['short_label'] = df['label'].apply(lambda x: x[:10])

    # Create a bar chart of the label distribution
    label_counts = df['short_label'].value_counts()
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(211)

    # Get the labels and their corresponding counts

    labels = label_counts.index
    counts = label_counts.values

    # Set the height of bars with zero counts to zero, making them invisible
    invisible_heights = [0 if count == 0 else count for count in counts]

    # Use the bar function to plot the bars
    ax.bar(labels, invisible_heights, width=0.3)

    ax.set_title('Label Counts')
    ax.set_xlabel('Label')
    ax.set_ylabel('Number of Examples')
    random_examples = df.sample(n=5)

    # Format the text column to show only the first 25 tokens
    random_examples['text'] = random_examples['text'].apply(
        lambda x: ' '.join(x.split()[:7]) + ('...' if len(x.split()) > 7 else ''))

    # Create a table to display the randomly selected examples
    table_data = [['Label', 'Text']]
    for _, row in random_examples.iterrows():
        table_data.append([row['short_label'], row['text']])

    table = ax.table(cellText=table_data, loc='bottom', cellLoc='left', bbox=[0, -1.2, 1, 0.5])

    table.auto_set_column_width(col=list(range(2)))
    # Create a string with the label and text for each example

    # Save the chart to a file
    plt.savefig("static/chart_prediction.png", dpi=100)

    return {"message": "Label distribution chart created successfully."}
