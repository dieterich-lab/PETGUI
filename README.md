# PETGUI
A more detailed progress tracking in PETGUI
## Setup
1. Clone and change directory to repository
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
## Run PET
- `uvicorn app.pet-gui:app --host 0.0.0.0 --port 8080`
- Open: http://10.250.135.122:8080/ in browser and navigate to /basic

- Input training parameters (small training data found in [data](/data/yelp_review_polarity_csv.tar.gz)), e.g.: ![Bildschirmfoto vom 2023-01-02 09-15-06](https://user-images.githubusercontent.com/47433679/210207339-edfcfea0-545c-41f3-aa8c-42e37acaa891.png)

- Training should start and finish in new window:
![Bildschirmfoto vom 2023-01-09 12-33-00](https://user-images.githubusercontent.com/47433679/211299773-e66d94d7-be85-4af4-894e-f5754d98458e.png)
![Bildschirmfoto vom 2023-01-09 12-36-02](https://user-images.githubusercontent.com/47433679/211299820-f2e2802c-12c6-48a6-a007-4bef817dc8f3.png)

- Prompt to download results as json file: ![Bildschirmfoto vom 2023-01-09 12-36-15](https://user-images.githubusercontent.com/47433679/211300377-40097403-fd64-4858-a231-2ff3d57661ca.png)
