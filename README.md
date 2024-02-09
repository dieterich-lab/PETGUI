# PETGUI

We present **PETGUI**: A user-friendly interface for training and testing a language model through <b>P</b>attern <b>E</b>xploiting <b>T</b>raining (<span style="font-style: italic">PET</span>) <a href="#pet" role="doc-noteref">[Schick et al., 2021]</a>.<br>


## 🔎 Contents
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
                        By reformulating input examples as cloze-style phrases, it has been shown to significantly outperform standard supervised training.


<figure>
  <img src="static/pet.png" width="50%">
    <figcaption style="font-size: 12px"><a href="#schick">Fig.1 - Schick et al., 2021</a></figcaption>
</figure>

In this illustration, the pattern <span style="font-style: italic">"It was ___ ."</span> is a cloze-style phrase, textually explaining to the model what the task is about,
in this case: <span style="font-style: italic;"> sentiment classification</span>. <br> For this, <span style="font-style: italic">PET</span> works in the following way: <br> A <b>P</b>retrained <b>L</b>anguage <b>M</b>odel is first trained on each of such patterns <strong>(1)</strong>. <br>
Secondly, an ensemble of these models annotates unlabeled training data <strong>(2)</strong>. <br> Finally, a classifier is trained on the resulting soft-labeled dataset <strong>(3)</strong>.</p>


<a id="requirements"></a>
### 🧰 PETGUI Requirements
* Docker=1.5-2
* Python=3.11
* torch=2.1.1 (on the server cluster)

To run **PETGUI** **locally** on your machine, you need:
1. A **working VPN connection** to an LDAP server.
2. **Ldap credentials** for accessing the server cluster.
3. `/home/<<user>>` directory in the server cluster.
4. The **ca-certificate file** for the server.


<a id="setup"></a>
### Setup PETGUI

First, in a terminal, `git clone` the repo and change directory to it.

#### Configuration
1. Adjust "train.sh" and "predict.sh" in [conf](/conf/train.sh) to your server's needs.
2. Now, inside `conf/`, create a file `conf.yaml` with the following contents (please adapt with your settings):
```
"LDAP_SERVER" : 'ldap://SERVER'
"CA_FILE" : 'NAME.pem'
"USER_BASE" : 'dc=XXX,dc=XXX'
"LDAP_SEARCH_FILTER" : '({name_attribute}={name})'
```
Please see the [example conf.yaml](/conf/conf.yaml) as a guide.  
3. Move the certificate file of the server (_.pem file_) into your `conf/` directory.  
4. Finally, build the docker image: `docker build . -t petgui`.  

<a id="start"></a>
### 🛫 Start PETGUI
First, make sure you are in the `PETGUI` repository directory.
1. Run the docker container: `docker run --name petgui -p 89:89 --mount type=bind,source=./conf,target=/home/appuser/conf petgui`.  
**For Windows, replace `./conf` with `\.conf`**  
This will start the app: 
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:89 (Press CTRL+C to quit)
```
2. Access it by opening localhost, e.g.: `http://127.0.0.1:89` in a browser.

<a id="run"></a>
### 👟️ Run PETGUI

Upon starting **PETGUI**, you will automatically be redirected to the Start page, where you can proceed to login.  
Whilst following the below steps, please follow the [guidelines](#training-parameter-guidelines) 

| Steps                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | What you will see             |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------|
| **1.** Login with your ldap credentials for your server:                                                                                                                                                                                                                                                                                                                                                                                                                                              | ![img_1.png](static/img_1.png) |
| **2.** Input training parameters: <br/> >> SAMPLE: **1**, LABEL: **0**<br/>>> TEMPLATE: **Es war _ .**<br/>>> VERBALIZER: 1 **schlecht**, 2 **gut**<br/> You may use the german few-shot training  [data](/data/GE-yelp_review_polarity_csv.tar.gz) and test [data](/data/predict.txt) available.<br/> By clicking `View Data`, you will have a preview of the data statistics of label distribution.                                                                                                 | ![img_3.png](static/img_3.png) |                               |
| **3.** Click `Submit` to proceed with your defined training parameters. `Start Training` will initiate the training process. You can `Abort` the process, which will stop the training and navigate you to step **2.**                                                                                                                                                                                                                                                                                | ![img_4.png](static/img_4.png) |
| **4.** `Show Results` to view the PET results. The results will display accuracy per pattern, as well as precision, recall, f1-measure, and support per label for each pattern. See "Final" for the final scores.                                                                                                                                                                                                                                                                                     | ![img_5.png](static/img_5.png) |
| **5.** Next, either re-train with new parameters (`Run with new configuration`) or use your trained model to label new data (`Annotate unseen data`).                                                                                                                                                                                                                                                                                                                                                 | ![img_6.png](static/img_6.png) |
| **6.** To annotate unlabeled data, use the sample file in [data](data/unlabeled.csv). First `Upload unlabeled data as a csv file` and make sure, that the first column in your dataset contains nothing throughout your data lines. `Predict Labels Using PET Model` will start the prediction process. When complete, download the generated prediction file: `Download Predicted Data`. | ![img_7.png](static/img_7.png) |

<a id="guidelines"></a>
#### 🧾 Training Parameter Guidelines
 * Include the underscore character: "_" in your templates, such that it acts as a placeholder, e.g.: "Es war \_ ." will become "Es war [verbalizer1]." and "Es war [verbalizer2].", with the verbalizers "gut" & "schlecht". 
 * Click `+` to add more verbalizers.  

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
In its current form, PETGUI is limited to training and testing a model on data in the following way:
* **VPN use:** You must have a working WireGuard VPN connection to the _Dieterich Lab_ server.
* **File format and naming convention:** The provided training data must be a <span style="font-style: italic">tar.gz</span> file
                                containing _train.csv_, _test.csv_ and _unlabeled.csv_ respectively.
                                For labeling data, a comma separated <span style="font-style: italic">.txt</span> file is expected with the first column throughout the data lines empty.
* **Verbalizer mapping:** The provided verbalizer has to map to a single input-id in the model vocabulary (no real-time check).

<a id="references"></a>  ​                     
### 🗃️ References
<ol style="margin-left: 17px; font-size: 15px;">
    <li id="pet">Timo Schick and Hinrich Schütze. (2021). Exploiting Cloze Questions for Few-Shot Text Classification and Natural Language Inference. arXiv preprint arXiv:2001.07676. Retrieved from <a href="https://arxiv.org/abs/2001.07676">(https://arxiv.org/abs/2001.07676)</a></li>
<li id="schick">Timo Schick. (2023). Pattern-Exploiting Training (PET) [GitHub repository]. Retrieved from <a href="https://github.com/timoschick/pet/">https://github.com/timoschick/pet/</a></li>
</ol>
