# PETGUI
A working training process in PETGUI
## Run Training and Prediction

|Steps|What you will see|
|---|-----|
|**1.** Open: http://10.250.135.12:8090/ in your browser and login with your cluster.dieterichlab.org server credentials: | ![image](https://user-images.githubusercontent.com/47433679/234077996-81853675-9680-43de-b2e7-42d4e1d879a4.png)|
|**2.** If successful, you will be redirected. Here you can input [training parameters](#note) (you may use the small training data available in [data](/data/yelp_review_polarity_csv.tar.gz)):| ![image](https://user-images.githubusercontent.com/47433679/234078268-c7231c78-7f87-4aa4-a6f7-0e2c08411cbf.png)|
|**3.** After clicking "Send", we will be ready to commence the training. Please click `Start Training` to initiate the training process:| ![image](https://user-images.githubusercontent.com/47433679/234080585-f2fbfd3b-77ab-433e-8484-6c2e796d4e88.png)|
|**4.** Upon completion of the training, you may select `Show Results` to view the PET results. The results will display accuracy per pattern, as well as precision, recall, f1-measure, and support per label for each pattern. The final scores are also included as "Final": | ![image](https://user-images.githubusercontent.com/47433679/234080878-b04a0774-ecf3-4c99-8358-6bdfe56ffd30.png)|
|**5.** Following the completion of the training, you will have the option to either conduct a new experiment or leverage the trained model to predict new data. This can be done by selecting either the `Run with new configuration` button, which will redirect you to the configuration page, or the `Annotate unseen data` button, which will redirect you to a new page where you can upload data and make predictions: | ![image](https://user-images.githubusercontent.com/47433679/234081128-7a8c0f06-f5f5-4008-844c-d593d784f40a.png)|
|**6.** When making predictions on new data, you may utilize the "Upload Unlabeled Text as Plain Text" button to upload the data. It is important that the data is in the same CSV format as the data used during training. To initiate the prediction process, please select `Predict Labels Using PET Model`. Upon completion of the prediction process, you can download the predicted file by clicking `Download Predicted Data`: | ![image](https://user-images.githubusercontent.com/47433679/234081485-90c1475b-8cc3-49a8-ba4f-8f4affa8e325.png)|

### <a name="note"></a> Guideline on training parameters
 * Make sure to include the underscore character: "\_" when defining your templates, such that it acts as a placeholder, for example: "It was \_ ." will become "It was verbalizer1." and "It was verbalizer2.", where verbalizer1 & verbalizer2 denote two verbalized labels (for example bad & good) 
 * More templates or more verbalizers can be added by using the `+` button. If you don't need it anymore, you can use the `-` button to delete it. 
