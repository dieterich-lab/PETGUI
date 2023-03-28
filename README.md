# PETGUI
A working training process in PETGUI
## Setup
**1.** Clone and change directory to repository
**2.** `python3 -m venv venv`
**3.** `source venv/bin/activate`
**4.** `pip install -r requirements.txt`
## Run Training
**1.** `uvicorn app.pet-gui:app --host 0.0.0.0 --port 8080`
**2.** Open: http://10.250.135.122:8080/ (if running on the cluster) or http://0.0.0.0:8080 (if running locally) in the browser and login with your cluster.dieterichlab.org server credentials: <kbd> ![image](https://user-images.githubusercontent.com/47433679/228178304-6839ceba-5172-4d74-a087-7cfc6bc577f4.png)</kbd>

**3.** If successful, you will be redirected to http://0.0.0.0:8080/basic. Here you can input training parameters (small training data available in [data](/data/yelp_review_polarity_csv.tar.gz)), e.g.: <kbd> ![Bildschirmfoto vom 2023-01-23 11-50-02](https://user-images.githubusercontent.com/47433679/214032245-2f29ddd4-2bb5-4238-82eb-e311fd44e2a3.png) </kbd>

* Make sure to include the underscore character: "\_" when defining your templates, such that it acts as a placeholder.
E.g.: "It was \_ ." will become "It was verbalizer1." and "It was verbalizer2.", where verbalizer1 & verbalizer2 denote two verbalized labels (for example bad & good)
* More templates or more verbalizers can be added by using the `+` button. If you don't need it anymore, you can use the `-` button to delete it.  

**4.** After clicking "Send", we will be ready to commence the training. Please click `Start Training` to initiate the training process: <kbd> ![Bildschirmfoto vom 2023-03-28 10-42-03](https://user-images.githubusercontent.com/47433679/228181319-9515cc71-691d-49d7-9fc4-ccf741fc8f4d.png) </kbd>
<kbd> ![Bildschirmfoto vom 2023-03-28 10-43-35](https://user-images.githubusercontent.com/47433679/228181531-0ef8c10a-af3d-404f-8531-547f741a8ed5.png) </kbd>

**5.** Upon completion of the training, you may select `Show Results` to view the PET results. The results will display accuracy per pattern, as well as precision, recall, f1-measure, and support per label for each pattern. The final scores are also included as "Final".   
<kbd> ![Bildschirmfoto vom 2023-03-15 08-46-19](https://user-images.githubusercontent.com/47433679/228183829-d8936b8e-dda5-465d-935d-7a146d666049.png) </kbd>


**6.** Following the completion of the training, you will have the option to either conduct a new experiment or leverage the trained model to predict new data. This can be done by selecting either the `Run with new configuration` button, which will redirect you to the configuration page, or the `Annotate unseen data` button, which will redirect you to a new page where you can upload data and make predictions. <kbd> ![alt text](https://user-images.githubusercontent.com/63499872/222561012-ac69c03a-1778-4e49-9b74-30bf1d1c30d3.jpeg) </kbd>

**7.** When making predictions on new data, you may utilize the "Upload Unlabeled Text as Plain Text" button to upload the data. It is important that the data is in the same CSV format as the data used during training. To initiate the prediction process, please select `Predict Labels Using PET Model`. Upon completion of the prediction process, you can download the predicted file by clicking `Download Predicted Data`. <kbd> ![Bildschirmfoto vom 2023-03-28 10-44-17](https://user-images.githubusercontent.com/47433679/228182263-3ac1ed17-2029-4b6d-8022-8f5ce38b5b98.png) </kbd>
