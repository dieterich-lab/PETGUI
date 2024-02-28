# PETGUI

We present PETGUI, a user-friendly graphical user interface for training,
testing and labeling with pre-trained masked language models using Pattern-Exploiting Training, a state-of-the-art machine learning framework for text classifica-
tion tasks using few-shot learning and prompting. Concretely, PETGUI facilitates
a multistep pipeline of training and testing on labeled data, followed by annotating
on unlabeled data in a comprehensible and intuitive way. PETGUI also provides
valuable insights into various aspects of the training, with statistics for label dis-
tribution and model performance. We envision our app as a pivotal use-case of a
simple Machine Learning application, that is accessible and manageable by users
without domain specific knowledge, in our case by physicians from clinical routine


## 🔎 Contents
- [Files](#files)
- [*Pattern Exploiting Training*](#pet)
- [🧰 PETGUI Requirements](#requirements)
- [⚙️ PETGUI Setup](#setup)
- [🛫 Start PETGUI](#start)
- [👟 Run PETGUI](#run)
  * [🧾 Training Parameter Guidelines](#guidelines)
- [➕ Features](#features)
- [➖ Limitations](#limitations)
- [🗃️ References](#references)

<a id="pet"></a>
### *Pattern Exploiting Training*
<p style="font-size: 15px;"><span style="font-style: italic">PET</span> is a <strong>semi-supervised training strategy for language models</strong>.
                        By reformulating input examples as cloze-style phrases, it has been shown to significantly outperform standard supervised training<a href="#schick"> (Schick et al., 2021)</a>.


<figure>
  <img src="static/pet.png" width="50%">
    <figcaption style="font-size: 12px">Fig.1 - Illustration of the PET workflow, see <a href="#schick">Schick et al., 2021</a></figcaption>
</figure>

In this illustration, the pattern <span style="font-style: italic">"It was ___ ."</span> is a cloze-style phrase, textually explaining to the model what the task is about,
in this case: <span style="font-style: italic;"> sentiment classification</span>. <br> For this, <span style="font-style: italic">PET</span> works in the following way: <br> A <b>P</b>retrained <b>L</b>anguage <b>M</b>odel is first trained on each of such patterns <strong>(1)</strong>. <br>
Secondly, an ensemble of these models annotates unlabeled training data <strong>(2)</strong>. <br> Finally, a classifier is trained on the resulting soft-labeled dataset <strong>(3)</strong>.</p>


<a id="requirements"></a>
### 🧰 PETGUI Requirements
* A Linux host system
* A connection to a remote Slurm cluster with GPUs, accessible via LDAP
* Docker=1.5-2
* Python=3.11
* torch=2.1.1 (on the server cluster)

To run **PETGUI** on your machine, you need:
1. A **working connection** to a remote Slurm cluster.
2. **Ldap credentials** for accessing the remote Slurm cluster.
3. The **ca-certificate file** for the remote Slurm cluster.

<a id="setup"></a>
### Installation

1. In a terminal, `git clone` the repo and change directory to it.
1. Modify Slurm configuration SBATCH lines of [train.sh](/conf/train.sh) and [predict.sh](/conf/predict.sh) to remote Slurm cluster's needs.
2. Create file `conf.yaml` inside `conf/` with the following contents (please adapt accordingly - [example conf file](/conf/example/conf.yaml)):
```
"LDAP_SERVER" : 'ldap://SERVER'
"CA_FILE" : 'NAME.pem'
"USER_BASE" : 'dc=XXX,dc=XXX'
"LDAP_SEARCH_FILTER" : '({name_attribute}={name})'
```
3. Move your certificate file of the server (_.pem file_) to `conf/` directory.  
4. Build docker image: `docker build . -t petgui`.  

<a id="start"></a>
### 🛫 Start PETGUI
1. Change directory to repository: `cd /PETGUI`
1. Run the docker container: `docker run --name petgui -p 89:89 --mount type=bind,source=./conf,target=/home/appuser/conf petgui` 
>INFO:     Started server process [1]  
>INFO:     Waiting for application startup.  
>INFO:     Application startup complete.  
>INFO:     Uvicorn running on http://0.0.0.0:89 (Press CTRL+C to quit)  

3. Open localhost, e.g.: `http://127.0.0.1:89` in a browser.

<a id="run"></a>
### 👟️ Run PETGUI

You successfully started **PETGUI**!   

| Steps                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | What you will see             |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------|
| **1.** Login with ldap credentials for your remote Slurm cluster:                                                                                                                                                                                                                                                                                                                                                                                                                             | ![img_1.png](static/img_1.png) |
| **2.** Input training parameters, e.g. for the german few-shot sample [data](/data/GE-yelp_review_polarity_csv.tar.gz): <br/> SAMPLE: **1**, LABEL: **0**<br/> TEMPLATE: **Es war _ .** (include underscore character: "_" as a separator in the template, </br>click "+" to add more)<br/> VERBALIZER: 1 **schlecht**, 2 **gut**<br/> Chose one of pre-defined language model: `gbert-base` or `medbert`.</br> Click `View Data` to get statistics on your data as label distribution plots. | ![img_3.png](static/img_3.png) |                               |
| **3.** Click `Submit` to proceed. `Start Training` to start the model training. You may `Abort` the process, which will terminate training</br> and navigate you to step **2.**                                                                                                                                                                                                                                                                                                               | ![img_4.png](static/img_4.png) |
| **4.** `Show Results` to view model results, displaying accuracy per pattern, as well as precision, recall, f1-measure, and support per label.                                                                                                                                                                                                                                                                                                                                                | ![img_5.png](static/img_5.png) |
| **5.** Choose to either re-train with new parameters (`Run with new configuration`) or continue wit trained model for labeling unseen data (`Annotate unseen data`).                                                                                                                                                                                                                                                                                                                          | ![img_6.png](static/img_6.png) |
| **6.**  Annotate unlabeled data, e.g. sample [data](/data/predict.txt): `Upload unlabeled data as a csv file` and make sure, that the first column in your dataset contains nothing throughout your data lines. `Predict Labels Using PET Model` starts prediction process. When complete, `Download Predicted Data`.                                                                                                                                                                         | ![img_7.png](static/img_7.png) |


### Stop PETGUI
In the terminal: `Ctrl + C to stop the running "uvicorn" process:
>^CINFO:     Shutting down  
>INFO:     Waiting for application shutdown.  
>INFO:     Application shutdown complete.  
>INFO:     Finished server process [1]
* To restart PETGUI:  
In the terminal:
1. `docker stop petgui`
2. `docker rm petgui`
3. `docker run...` from [2.](#-start-petgui)


<a id="features"></a>
### ➕ Features
This GUI offers a step-by-step approach to training and deploying a language model on PET. Concretely, with PETGUI you can choose to:

* <strong>Train</strong> either <span style="font-style: italic">bert-base-cased</span> or <span style="font-style: italic">medbert-512</span> on a labeled dataset
* <strong>Label</strong> data using the trained model
* View statistics on <b>model performance</b> during training
* Download the produced file with <strong>labeled</strong> data
* View the <b>label distribution statistics</b> of training data

<a id="limitations"></a>
### ➖ Limitations
In its current form, PETGUI is bound to following requisites, which we may further simplify in future work:
* **VPN use:** You must have a working connection to a remote Slurm cluster.
* **File format and naming convention:** The provided training data must be a <span style="font-style: italic">tar.gz</span> file
                                containing _train.csv_, _test.csv_ and _unlabeled.csv_ respectively, like our [sample training data](data/train.tar.gz).
                                For labeling data, a comma separated <span style="font-style: italic">.txt</span> file is expected with the first column throughout the data lines empty, like our [sample test data](data/predict.txt).
* **Verbalizer mapping:** The tokenizer splits words into sub-words, e.g.: "Langeswort" becomes "Langes" and "#wort".  
The provided verbalizer has to map to a single input-id, hence the user must provide a sub-word from the model vocabulary. </br> We plan on adding user feedback to ensure correct input.

<a id="references"></a>  ​                     
### 🗃️ References
<ol style="margin-left: 17px; font-size: 15px;">
    <li id="pet">Timo Schick and Hinrich Schütze. (2021). Exploiting Cloze Questions for Few-Shot Text Classification and Natural Language Inference. arXiv preprint arXiv:2001.07676.</a></li>
    <li id="schick">Timo Schick. (2023). Pattern-Exploiting Training (PET) <a href="https://github.com/timoschick/pet/">GitHub repository</a></li>
    <li id="mie">Richter-Pechanski P, Wiesenbach P, Schwab DM, Kiriakou C, He M, Geis NA, Frank A, Dieterich C. Few-Shot and Prompt Training for Text Classification in German Doctor's Letters. Stud Health Technol Inform. 2023 May 18;302:819-820. doi: 10.3233/SHTI230275. PMID: 37203504.
</ol>
