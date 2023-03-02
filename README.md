# PETGUI
A working training process in PETGUI
## Setup
1. Clone and change directory to repository
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
## Run Training
1. `uvicorn app.pet-gui:app --host 0.0.0.0 --port 8080`
2. Open: http://10.250.135.122:8080/ (if running on the cluster) or http://0.0.0.0:8080 (if running locally) in the browser and it will navigate to http://0.0.0.0:8080/basic automatically

3. Input training parameters (small training data available in [data](/data/yelp_review_polarity_csv.tar.gz)), e.g.: ![Bildschirmfoto vom 2023-01-23 11-50-02](https://user-images.githubusercontent.com/47433679/214032245-2f29ddd4-2bb5-4238-82eb-e311fd44e2a3.png)

* Make sure to include the underscore character: "\_" when defining your templates, such that it acts as a placeholder.
E.g.: "It was \_ ." will become "It was verbalizer1." and "It was verbalizer2.", where verbalizer1 & verbalizer2 denote two verbalized labels (for example bad & good)
* More templates or more verbalizers can be added by using the "+" button. If you don't need it anymore, you can use the "-" button to delete it.  

4. After clicking "Send", we will be ready to commence the training. Please click "Start Training" to initiate the training process:![Bildschirmfoto vom 2023-01-23 11-54-02](https://user-images.githubusercontent.com/63499872/221887170-dea033d7-2272-4577-b6b6-40b377c7a512.jpeg)

5. Upon completion of the training, you may select "Download Results" to view the PET results. The results will display accuracy per pattern, as well as precision, recall, f1-measure, and support per label for each pattern. The final scores are also included as "Final". Furthermore, the results will be available for download as JSON data.![Bildschirmfoto vom 2023-02-17 14-40-29](https://user-images.githubusercontent.com/63499872/221966737-b871dfa5-3d15-486f-ab1d-fb72f3544312.jpeg)

6. After the training, you can choose whether to run a new experiment or to use the trained model to predict new data by clicking the botton "Run with new configuration", where you will be redirected to the configuration page,  or "Annotate unseen data", where you will be redirected to a new page where you can upload data and predict:![alt text](https://user-images.githubusercontent.com/63499872/221894674-7b3ab607-943f-4df7-bac5-42e5612c1ec8.png)
