# PETGUI

We introduce **PETGUI**: A user-friendly interface for training and testing a language model through <b>P</b>attern <b>E</b>xploiting <b>T</b>raining (<span style="font-style: italic">PET</span>) <a href="#pet" role="doc-noteref">[Schick et al., 2021]</a>.<br>


## 🔎 Contents
+ [*Pattern Exploiting Training*](#-pattern-exploiting-training-)
+ [PETGUI Requirements](#petgui-requirements)
+ [Start PETGUI](#start-petgui)
+ [Run PETGUI](#run-petgui)
  - [Training Parameter Guidelines](#training-parameter-guidelines)
+ [Limitations](#limitations)
+ [References](#references)
+ [TODOs](#todos)

### *Pattern Exploiting Training*
<p style="font-size: 15px;"><span style="font-style: italic">PET</span> is a <strong>semi-supervised training strategy for language models</strong>.
                        By reformulating input examples as cloze-style phrases, it has been shown to significantly outperform standard supervised training.


<figure>
  <img src="static/pet.png" width="50%">
    <figcaption style="font-size: 12px"><a href="#schick">Fig.1 - Schick et al., 2021</a></figcaption>
</figure>

In this illustration, the pattern <span style="font-style: italic">"It was ___ ."</span> is a cloze-style phrase, textually explaining to the model what the task is about,
in this case: <span style="font-style: italic;"> sentiment classification</span>. <br> For this, <span style="font-style: italic">PET</span> works in the following way: <br> A <b>P</b>retrained <b>L</b>anguage <b>M</b>odel is first trained on each of such patterns <strong>(1)</strong>. <br>
Secondly, an ensemble of these models annotates unlabeled training data <strong>(2)</strong>. <br> Finally, a classifier is trained on the resulting soft-labeled dataset <strong>(3)</strong>.</p>



### 🧰 PETGUI Requirements
To run **PETGUI** **locally** on your machine, you need a **working VPN connection** to the *DieterichLab* server and **ldap credentials** for accessing the *DieterichLab* cluster at: *[username]@cluster.dieterichlab.org*.  
You may then proceed with the following steps:
1. Clone this repository using `git clone …`, either through *HTTPS*: `https://github.com/dieterich-lab/xai-in-nlp.git` or *SSH*: `git@github.com:dieterich-lab/xai-in-nlp.git`
2. Create and activate a Python3 virtual environment: `python3 -m venv venv` & `source venv/bin/activate`
3. Install all madatory packages in requirements.txt: `pip install -r requirements.txt`

### 🛫 Start PETGUI
To start **PETGUI locally** on your machine, open you terminal in the repository folder */PETGUI* and input the bash command: `uvicorn app.petGui:app`.  
This will open the application in a new browser tab under your localhost address. Simply click the link to your localhost in the response body: 

```
(venv) ~/PETGUI$ uvicorn app.petGui:app

INFO:     Started server process [22919]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

```
### ⚙️ Run PETGUI

Upon starting **PETGUI**, you will automatically be redirected to the Start page, where you can proceed to login.  
Whilst following the below steps, please follow the [guidelines](#training-parameter-guidelines) 

| Steps                                                                                                                                                                                                                                                                                                                                                                                                                                                            | What you will see                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1.** Login with your ldap credentials for the *DieterichLab* server:                                                                                                                                                                                                                                                                                                                                                                                           | ![img_1.png](img_1.png)                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **2.** If successful, you will be redirected. Here you can input [training parameters](img_3.png) (you may use the german few-shot training  [data](/data/GE-yelp_review_polarity_csv.tar.gz) available) By clicking `View Data`, you will have a preview of the data statistics of label distribution.                                                                                                                                                          | ![img_3.png](img_3.png)                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **3.** Click `Submit` to proceed with your defined training parameters. `Start Training` will initiate the training process. You can `Abort` the process, which will stop the training and navigate you to step **2.**                                                                                                                                                                                                                                           | ![img_4.png](img_4.png)                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **4.** Upon completion of the training, you may select `Show Results` to view the PET results. The results will display accuracy per pattern, as well as precision, recall, f1-measure, and support per label for each pattern. The final scores are also included as "Final":                                                                                                                                                                                   | ![img_5.png](img_5.png)                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **5.** Next, you have the option to either re-train with new parameters (`Run with new configuration`) or use your trained model to label new data (`Annotate unseen data`).                                                                                                                                                                                                                                                                                     | ![img_6.png](img_6.png)                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **6.** To annotate unlabeled data, first `Upload unlabeled data as a csv file` and make sure, that the first column in your dataset contains nothing throughout your data lines. `Predict Labels Using PET Model` will start the prediction process. Upon completion, you may download the generated prediction file with `Download Predicted Data`. `Show Chart` will display the label distribution of the annotated file, along with some sample annotations: | ![img_7.png](img_7.png)|

#### 🧾 Training Parameter Guidelines
 * Make sure to include the underscore character: "_" when defining your templates, such that it acts as a placeholder, for example: "Es war \_ ." will become "Es war [verbalizer1]." and "Es war [verbalizer2].", with the verbalizers denoting textualized labels, e.g. bad & good. 
 * You may add more templates and verbalizers by clicking `+` and removing with `-`.  

### ➕ Features
This GUI offers a step-by-step approach to training and deploying a language model on PET. Concretely, with PETGUI you can choose to:

* <strong>Train</strong> either <span style="font-style: italic">bert-base-cased</span> or <span style="font-style: italic">medbert-512</span> on a labeled dataset
* <strong>Label</strong> data using the trained model
* View statistics on <b>model performance</b> during training
* Download the produced file with <strong>labeled</strong> data
* View <b>label distribution statistics</b> of training data and labeled data

### ➖ Limitations
In its current form, PETGUI is limited to training and testing a model on data in the following way:
* **VPN use:** You must have a working WireGuard VPN connection to the _Dieterichlab_ server.
* **File format and naming convention:** The provided training data must be a <span style="font-style: italic">tar.gz</span> file
                                containing <span style="font-style: italic">train.csv</span> and <span style="font-style: italic">test.csv</span> respectively.
                                For the unlabeled data, a <span style="font-style: italic">.csv</span> file is expected with the first column throughout the data lines empty.
* **Maximum capacity:** The max number of definable patterns for one training pass is 5

  ​                     
### 🗃️ References
<ol style="margin-left: 17px; font-size: 15px;">
    <li id="pet">Timo Schick and Hinrich Schütze. (2021). Exploiting Cloze Questions for Few-Shot Text Classification and Natural Language Inference. arXiv preprint arXiv:2001.07676. Retrieved from <a href="https://arxiv.org/abs/2001.07676">(https://arxiv.org/abs/2001.07676)</a></li>
<li id="schick">Timo Schick. (2023). Pattern-Exploiting Training (PET) [GitHub repository]. Retrieved from <a href="https://github.com/timoschick/pet/">https://github.com/timoschick/pet/</a></li>
</ol>


### ❎ TODOs         
- [ ] **Add sample line of training data** for user to see according column numbers for data and labels
- [ ] If unlabeled data is not included in training data, **use training data in place of it**
- [ ] **Warn user about inconsistent language** in training data and its parameter definitions
- [ ] Implement **"Hide table"** for model performance statistics
- [ ] **Display file guideline** for predictions on last page
- [ ] …
- [ ] **On unconventional shutdown** (no logout): 
  * abort processes
  * delete created user folder structure after some time  
    