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
3. Input training parameters (small training data found in [data](/data/yelp_review_polarity_csv.tar.gz)), e.g.: ![Bildschirmfoto vom 2023-01-02 09-15-06](https://user-images.githubusercontent.com/63499872/212850711-d52e55ca-2189-465a-b3e8-023a94d09af9.jpeg)
More templates or more verbalizers could be added by using the "+" button. If you don't need it anymore, you can use the "-" button to delete it.
4. Training should start and finish in new window: ![Bildschirmfoto vom 2023-01-02 08-36-02](https://user-images.githubusercontent.com/47433679/210207440-ad3f410d-3ce3-48c8-b4f6-da3c44b6d0bb.png)
![Bildschirmfoto vom 2023-01-02 09-06-46](https://user-images.githubusercontent.com/47433679/210207594-5ba1d3a3-a633-404e-8a82-42e862d12155.png)


