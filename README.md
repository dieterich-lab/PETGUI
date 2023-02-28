# PETGUI
A working training process in PETGUI
## Setup
1. Clone and change directory to repository
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
## Run Training
1. `uvicorn app.pet-gui:app --host 0.0.0.0 --port 8080`
2. Open: http://10.250.135.122:8080/ (if running on the cluster) or http://0.0.0.0:8080 (if running locally) in the browser and navigate to http://0.0.0.0:8080/basic

3. Input training parameters (small training data available in [data](/data/yelp_review_polarity_csv.tar.gz)), e.g.: ![Bildschirmfoto vom 2023-01-23 11-50-02](https://user-images.githubusercontent.com/47433679/214032245-2f29ddd4-2bb5-4238-82eb-e311fd44e2a3.png)

* Make sure to include the underscore character: "\_" when defining your templates, such that it acts as a placeholder.
E.g.: "It was \_ ." will become "It was verbalizer1." and "It was verbalizer2.", where verbalizer1 & verbalizer2 denote two verbalized labels (for example bad & good)
* More templates or more verbalizers can be added by using the "+" button. If you don't need it anymore, you can use the "-" button to delete it.  

4. After clicking "Send", we are prepared for the training!Click the "Start Training" to start the training process:![Bildschirmfoto vom 2023-01-23 11-54-02](https://user-images.githubusercontent.com/63499872/221887170-dea033d7-2272-4577-b6b6-40b377c7a512.jpeg)

5. Once the training is completed,you can click on "Download Results", where results of PET will be displayed as accuracy per pattern as well as precision, recall, f1-measure and support per label for each pattern. Final scores are also included as "Final".The result will also be downloaded as json data![Bildschirmfoto vom 2023-02-17 14-40-29](https://user-images.githubusercontent.com/63499872/221890217-70bbc14c-83a1-428d-8023-ca1c80167dbd.jpeg)

6. After the training, you can choose whether to run a new experiment or to use the trained model to predict new data by clicking the botton "Run with new configuration", where you will be redirected to the configuration page,  or "Annotate unseen data", where you will be redirected to a new page where you can upload data and predict:![alt text](https://user-images.githubusercontent.com/63499872/221894674-7b3ab607-943f-4df7-bac5-42e5612c1ec8.png)
