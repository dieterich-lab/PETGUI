# PETGUI
A working training process in PETGUI

## Pattern Exploiting Training
PET was introduced in 2020 as a semi-supervised training strategy for language models. By reformulating input examples as cloze-style phrases, PET has been shown to significantly outperform standard supervised training.

In this illustration, the pattern "It was ___ ." is a cloze-style phrase, textually explaining to the model what the task is about, in this case: sentiment classification.
For this, PET works in the following way: A Pretrained Language Model is first trained on each of such patterns (1).
Secondly, an ensemble of these models annotates unlabeled training data (2).
Finally, a classifier is trained on the resulting soft-labeled dataset. (3).

![Image](https://user-images.githubusercontent.com/63499872/245711289-23f4440f-1116-40ea-8447-1af20abff25c.png)

## Requirements

## Install/Start application

## Run Training and Prediction

| Steps                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |What you will see|
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----|
| **1.** Open: http://10.250.135.12:8090/ in your browser and login with your cluster.dieterichlab.org server credentials:                                                                                                                                                                                                                                                                                                                                                                                                                                                           | ![image](https://user-images.githubusercontent.com/47433679/234077996-81853675-9680-43de-b2e7-42d4e1d879a4.png)|
| **2.** If successful, you will be redirected. Here you can input [training parameters](#note) (you may use the small training data available in [data](/data/yelp_review_polarity_csv.tar.gz)) By clicking 'View Data,' you will have a preview of the data statistics. By clicking the same position (the button will automatically change to 'Hide Data'), the statistics image will be hidden:                                                                                                                                                                                  | ![image](https://user-images.githubusercontent.com/63499872/244614019-cbe6c7d8-3d5f-411c-b905-455bb06d299b.png)|
| **3.** After clicking "Send", we will be ready to commence the training. Please click `Start Training` to initiate the training process:                                                                                                                                                                                                                                                                                                                                                                                                                                           | ![image](https://user-images.githubusercontent.com/47433679/234080585-f2fbfd3b-77ab-433e-8484-6c2e796d4e88.png)|
| **4.** Upon completion of the training, you may select `Show Results` to view the PET results. The results will display accuracy per pattern, as well as precision, recall, f1-measure, and support per label for each pattern. The final scores are also included as "Final":                                                                                                                                                                                                                                                                                                     | ![image](https://user-images.githubusercontent.com/47433679/234080878-b04a0774-ecf3-4c99-8358-6bdfe56ffd30.png)|
| **5.** Following the completion of the training, you will have the option to either conduct a new experiment or leverage the trained model to predict new data. This can be done by selecting either the `Run with new configuration` button, which will redirect you to the configuration page, or the `Annotate unseen data` button, which will redirect you to a new page where you can upload data and make predictions:                                                                                                                                                       | ![image](https://user-images.githubusercontent.com/47433679/234081128-7a8c0f06-f5f5-4008-844c-d593d784f40a.png)|
| **6.** When making predictions on new data, you may utilize the "Upload unlabeled data as a csv file" button to upload the data. It is important that the data is in the same CSV format as the data used during training. To initiate the prediction process, please select `Predict Labels Using PET Model`. Upon completion of the prediction process, you can download the predicted file by clicking `Download Predicted Data`. By clicking 'Show Chart,' the label distribution of the data will be displayed, along with five randomly selected examples of predicted data: | ![image](https://user-images.githubusercontent.com/63499872/244616169-ad0e037b-69da-4be7-9313-72a9dc656b36.png)|

### <a name="note"></a> Guideline on training parameters
 * Make sure to include the underscore character: "\_" when defining your templates, such that it acts as a placeholder, for example: "It was \_ ." will become "It was verbalizer1." and "It was verbalizer2.", where verbalizer1 & verbalizer2 denote two verbalized labels (for example bad & good) 
 * More templates or more verbalizers can be added by using the `+` button. If you don't need it anymore, you can use the `-` button to delete it. 


### <a name="limitations"></a> Limitations
In its current form, PETGUI is limited to training and testing a model on data in the following way:
* **VPN use:** You must have a working WireGuard VPN connection to the _Dieterichlab_ server.
* **File format and naming convention:** The provided training data must be a <span style="font-style: italic">tar.gz</span> file
                                containing <span style="font-style: italic">train.csv</span> and <span style="font-style: italic">test.csv</span> respectively.
                                For the unlabeled data, a <span style="font-style: italic">.txt</span> file is expected with a comma (",") as a separator in the
                                first colum at the beginning of each line
* **Maximum capacity:** The max number of definable patterns for one training pass is 5

### <a name="TODOS"></a> TODOs         

### <a name="References"></a> References
[1] Timo Schick and Hinrich Schütze. (2021). Exploiting Cloze Questions for Few-Shot Text Classification and Natural Language Inference. arXiv preprint arXiv:2001.07676. Retrieved from [https://arxiv.org/abs/2001.07676](https://arxiv.org/abs/2001.07676)


[2] Timo Schick. (2023). Pattern-Exploiting Training (PET) [GitHub repository]. Retrieved from [https://github.com/timoschick/pet/](https://github.com/timoschick/pet/)
