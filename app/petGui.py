from fastapi import FastAPI, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import json
import os
import threading
import time
import subprocess
from subprocess import PIPE
from app.controller import templating
from app.controller.templating import SessionData, UUID


from .controller.templating import get_session_id, get_session_data



'''START APP'''
app = FastAPI()
'''Include routers'''
app.include_router(templating.router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/steps", name="steps", dependencies=[Depends(get_session_id)])
def get_steps(session_id: UUID = Depends(get_session_id)):
    with open(f"./{hash(session_id)}/data.json") as f:
        data = json.load(f)
    count_tmp = len([tmp for tmp in data.keys() if "template_" in tmp])
    count_steps = 18 + (count_tmp-1) * 5
    return {"steps": count_steps}


@app.get("/", name="start")
def main():
    return RedirectResponse(url="/login")


@app.get("/whoami", dependencies=[Depends(get_session_id), Depends(get_session_data)], name="whoami")
def whoami(session_id: UUID = Depends(get_session_id), session_data: SessionData = Depends(get_session_data)):
    return session_id, session_data


@app.get("/logging/start_train",  dependencies=[Depends(get_session_id), Depends(get_session_data)])
async def run(session_id: UUID = Depends(get_session_id), session_data: SessionData = Depends(get_session_data)):
    """
    Kicks off PET by calling train method.
    """
    '''Start PET'''
    print("Training starting..")
    job_id = await submit_job(session_data, False, session_id)
    t = threading.Thread(target=check_job_status, args=(job_id, session_data, False, session_id))
    t.start()

async def submit_job(session_data: SessionData = Depends(get_session_data), predict: bool = False, session_id: UUID = Depends(get_session_id)):
    # Copy the SLURM script file to the remote cluster
    print("Submitting job..")

    user = session_data.username
    remote_loc = session_data.remote_loc
    remote_loc_pet = session_data.remote_loc_pet
    cluster_name = session_data.cluster_name

    if predict:
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

def bash_cmd(cmd, session_id: UUID = Depends(get_session_id), shell:bool = False):
    proc = subprocess.Popen(" ".join(cmd) if shell else cmd, env={"SSHPASS": os.environ[f"{hash(session_id)}"]}, shell=shell,
                            stdout=subprocess.PIPE, stderr=PIPE)
    outs, errs = proc.communicate()
    return outs, errs


def check_job_status(job_id: str, session_data: SessionData = Depends(get_session_data), predict: bool = False,
                     session_id: UUID = Depends(get_session_id)):
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

        time.sleep(5)

        ssh_cmd = ['sshpass', '-e', 'ssh', f'{user}@{cluster_name}',
                   f'cat /home/{user}/{log_file.split("/")[-1]}']
        outs, errs = bash_cmd(ssh_cmd, session_id)
        log_contents = outs.decode('utf-8')

        # Update the log file on the local machine
        with open(f"{log_file}", 'w') as f:
            f.write(log_contents)


def results(session_id: UUID = Depends(get_session_id)):
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
        

@app.get("/final/start_prediction", dependencies=[Depends(get_session_id), Depends(get_session_data)])
async def label_prediction(session_data: SessionData = Depends(get_session_data), session_id: UUID = Depends(get_session_id)):
    '''Start Predict'''
    job_id = await submit_job(session_data, True, session_id)
    return check_job_status(job_id, session_data, True, session_id)
