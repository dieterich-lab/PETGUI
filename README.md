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

4. Training should start and finish in new window: ![Bildschirmfoto vom 2023-01-23 11-54-02](https://user-images.githubusercontent.com/47433679/214032285-5865ae18-8924-4aae-bfaf-fd59d03a0ec3.png)

5. Click on "See Results", where results of PET will be displayed as accuracy per pattern as well as precision, recall, f1-measure and support for each label per pattern. Please note that final results may take longer to be processed: ![image](https://user-images.githubusercontent.com/47433679/217211299-2ac3bccb-aec8-4688-8b17-7ed1805d8801.png)  
Reloading page after a few minutes will display complete results, hence can be downloaded as json file.

