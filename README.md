# PETGUI
A working training process in PETGUI
## Setup
1. Clone and change directory to repository
2. `python3 -m venv venv`
3. `source venv/bin/activate`
4. `pip install -r requirements.txt`
## Run Training
1. `uvicorn app.pet-gui:app --host 0.0.0.0 --port 8080`


  More templates or more verbalizers could be added by using the "+" button. If you don't need it anymore, you can use the "-" button to delete it.

4. Training should start and finish in new window:
![Bildschirmfoto vom 2023-01-09 12-33-00](https://user-images.githubusercontent.com/47433679/211299773-e66d94d7-be85-4af4-894e-f5754d98458e.png)
![Bildschirmfoto vom 2023-01-09 12-36-02](https://user-images.githubusercontent.com/47433679/211299820-f2e2802c-12c6-48a6-a007-4bef817dc8f3.png)

- Prompt to download results as json file: ![Bildschirmfoto vom 2023-01-09 12-36-15](https://user-images.githubusercontent.com/47433679/211300377-40097403-fd64-4858-a231-2ff3d57661ca.png)

