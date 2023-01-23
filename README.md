# PETGUI
A working training process in PETGUI
## Setup
1. Clone and change directory to repository
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
## Run Training
1. `uvicorn app.pet-gui:app --host 0.0.0.0 --port 8080`

2. Open: http://10.250.135.122:8080/(in cluster) or http://0.0.0.0:8080 (local) in browser and navigate to /basic

3. Input training parameters (small training data found in [data](/data/yelp_review_polarity_csv.tar.gz)), e.g.: ![Bildschirmfoto vom 2023-01-23 11-50-02](https://user-images.githubusercontent.com/47433679/214032245-2f29ddd4-2bb5-4238-82eb-e311fd44e2a3.png)

More templates or more verbalizers could be added by using the "+" button. If you don't need it anymore, you can use the "-" button to delete it.  

4. Training should start and finish in new window: ![Bildschirmfoto vom 2023-01-23 11-54-02](https://user-images.githubusercontent.com/47433679/214032285-5865ae18-8924-4aae-bfaf-fd59d03a0ec3.png)

5. Click on "See Results", where results of PET will be displayed as accuracies per pattern. Please note that final results may take longer to be processed: ![Bildschirmfoto vom 2023-01-23 12-06-32](https://user-images.githubusercontent.com/47433679/214032841-4a808baa-f7c8-4552-951e-82feb84e159e.png)  
Reloading page after a few minutes will complete results, hence can be downloaded as json file:  
![Bildschirmfoto vom 2023-01-23 12-11-03](https://user-images.githubusercontent.com/47433679/214033043-74e45b3c-80ba-4af7-beed-e0be176f6205.png)



