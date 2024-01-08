import json
import time
from uuid import uuid4
from fastapi import Request, Response
from fastapi.testclient import TestClient
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from app.controller import templating
from app.petGui import app, get_session
import pytest
from fastapi.responses import FileResponse, RedirectResponse
from app.dto.session import SessionData
import io
import os
from os.path import exists
import pandas as pd
from pathlib import Path
from .in_memory_backend_mock import InMemoryBackendMock
import matplotlib


class TestServer:

    matplotlib.use('agg')

    session_id = uuid4()
    session_data = SessionData(
        username="username",
        id=session_id,
        remote_loc="remote_location",
        remote_loc_pet="remote_location_pet",
        cluster_name="cluster_name",
        last_pos_file=f"{hash(session_id)}/last_pos_file.txt",
        log_file=f"{hash(session_id)}/log_file.txt",
        job_id=None, event=None, job_status=None
    )
    data = {"username": "user", "password": "pass"}

    @pytest.fixture
    def browser(self):
        # Initialize the Chrome WebDriver
        service = ChromeService(executable_path=ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.implicitly_wait(20)
        yield driver
        # Clean up after the tests
        driver.quit()

    @pytest.fixture()
    def setting(self):
        self.metadata = {
            "sample": "1",
            "label": "0",
            "template_0": "Dieser Text berichtet über _.",
            'origin_0': 'AllergienUnverträglichkeitenRisiken', 'origin_1': 'Anamnese', 'origin_2': 'Befunde',
            'origin_3': 'Diagnosen', 'origin_4': 'Medikation', 'origin_5': 'Other', 'mapping_0': 'Risiko',
            'mapping_1': 'Vorstellung', 'mapping_2': 'Nachweis', 'mapping_3': 'Diagnose', 'mapping_4': 'Medikamente',
            'mapping_5': 'Verlauf',
            "m_para": "gbert-base"
        }
        yield self.metadata,

    @pytest.fixture
    def test_client(self, mocker):
        self.client = TestClient(app, base_url="https://petgui.dieterichlab.org")
        self.request = Request
        self.response = Response
        self.mock_response = mocker.MagicMock(self.response)
        self.mock_request = mocker.MagicMock(self.request)
        yield self.client

    def test_home(self, test_client):
        print("Testing app start..")
        response = self.client.get("/")
        assert response.status_code == 200

    def test_start(self, test_client):
        print("Testing start..")
        response = self.client.get("/start")
        assert response.status_code == 200

    def test_login(self, test_client):
        print("Testing login..")
        response = self.client.get("/login")
        assert response.status_code == 200

    @pytest.fixture
    def mock_get_session_service(self):
        yield self.session_data

    @pytest.fixture
    def mock_session(self, mock_get_session_service, test_client):
        self.mock_get_session_service = mock_get_session_service

        app.dependency_overrides[get_session] = lambda: self.mock_get_session_service
        app.dependency_overrides[templating.get_session] = lambda: self.mock_get_session_service
        yield self.mock_get_session_service


    @pytest.fixture
    def helper_mock(self, mocker):
        mocker.patch("app.services.session.create_session", return_value=self.mock_get_session_service)

    @pytest.fixture
    def mock_create_session(self):
        os.environ[f"{hash(self.session_id)}"] = self.data["password"]

    @pytest.fixture
    def mock_user_dn(self, mocker):
        mocker.patch("app.services.ldap.get_dn_of_user", return_value=self.session_data.username)  # Return user dn

    @pytest.fixture
    def mock_bind(self, mocker):
        mocker.patch("app.services.ldap.bind", return_value=True)  # Return user authentication

    @pytest.fixture
    def mock_login(self, mocker): # Not a necessity
        response = RedirectResponse(url=self.mock_request.url_for("homepage"), status_code=303)
        mocker.patch("app.controller.session.login", return_value=response)

    def test_login_form(self, test_client, mock_user_dn, mock_bind, mock_create_session, mock_login, mock_backend_create):
        print("Testing login..")
        response = self.client.post("/login", data=self.data)
        assert response.status_code == 200

    def test_whoami(self, test_client, mock_session):
        print("Testing whoami..")
        response = self.client.get("/whoami")
        assert self.session_data.username in response.content.decode("utf-8")
        assert response.status_code == 200

    def test_basic(self, test_client, mock_session):
        print("Testing basic..")
        response = self.client.get("/basic")
        assert response.status_code == 200

    def test_logging(self, test_client, mock_session):
        print("Testing logging..")
        response = self.client.get("/logging", params={"error": None})
        assert response.status_code == 200

    def test_extract_file(self, test_client, setting, mock_session):
        print("Testing extract file")
        with open("data/train.tar.gz", "rb") as tar_file:
            response = self.client.post("/extract-file", files={"file": ("data.tar.gz", tar_file)})
        assert exists(f"{hash(self.session_id)}/data_uploaded/data/train.csv")
        assert exists(f"{hash(self.session_id)}/data_uploaded/data/test.csv")
        assert exists(f"{hash(self.session_id)}/label_dict.json")
        assert exists("static/chart.png")
        assert response.status_code == 200
        assert response.json() == {"message": "File extracted successfully."}

    def test_report_labels(self, test_client, mock_session):
        print("Testing report labels")
        response = self.client.get(url="/report-labels")
        assert "list" in response.json()
        assert response.status_code == 200

    def test_homepage(self, test_client, setting, mock_session):
        print("Testing homepage..")
        with open("data/train.tar.gz", "rb") as f:
            data = io.BytesIO(f.read())
        file = {"file": ("train", data, "multipart/form-data")}
        response = self.client.post(
            "/basic",
            data=self.metadata,
            files=file,
            follow_redirects=False
        )
        assert response.status_code == 303
        assert f"{response.next_request}" == f"{self.client.get('/logging', follow_redirects=False).request}"
        assert exists(f"{hash(self.session_id)}/data_uploaded")
        assert exists(f"{hash(self.session_id)}/data.json")
        assert exists(f"{self.session_data.log_file}")

    @pytest.fixture
    def mock_submit_job(self, mocker):
        mocker.patch("app.petGui.submit_job", return_value="1234")  # Return job-id

    @pytest.fixture
    def mock_check_job(self, mocker):
        mocker.patch("app.petGui.check_job_status", return_value="CD")  # Return job-status

    def test_logging_train(self, test_client, mock_session, mock_submit_job, mock_check_job, mock_backend_update):
        print("Testing training..")
        response = self.client.get("/logging/start_train")
        assert response.status_code == 200

    def test_get_steps(self, test_client, mock_session):
        print("Testing get steps..")
        response = self.client.get("/steps")
        assert response.json() == {"steps": 18}
        assert response.status_code == 200

    def test_read_log(self, test_client, mock_session):
        print("Testing read log..")
        response = self.client.get("/log")
        assert exists(self.session_data.last_pos_file)
        assert response.json() == {"log": []}
        assert response.status_code == 200

    @pytest.fixture
    def mock_results(self, mock_session):

        with open(f"{hash(self.session_id)}/results.json", "w") as f:
            json.dump({
        "train_set_before_training": 0.18333333333333332,
        "global_step": 114,
        "average_loss": 0.6888206180250436,
        "train_set_after_training": 0.7166666666666667,
        "test_set_after_training":
            {"acc": 0.6944444444444444,
             "pre-rec-f1-supp": [
                 [0.8181818181818182, 0.7241379310344828, 1.0, 0.5384615384615384, 0.9615384615384616, 0.5],
                 [0.9, 0.7, 0.26666666666666666, 0.9333333333333333, 0.8333333333333334, 0.5333333333333333],
                 [0.8571428571428572, 0.711864406779661, 0.4210526315789474, 0.6829268292682926, 0.8928571428571429, 0.5161290322580646],
                 [30, 30, 30, 30, 30, 30]]}}, f)
        yield FileResponse(f"{hash(self.session_id)}")

    def test_download(self, test_client, mock_session, mock_results):
        print("Testing results..")
        response = self.client.get("/download")
        assert exists(f"{hash(self.session_id)}/results.json")
        assert response.status_code == 200
        #assert exists(f"{hash(self.session_id)}/output")

    def test_final(self, test_client, mock_session):
        print("Testing final..")
        response = self.client.get("/final")
        assert response.status_code == 200

    def test_upload_file(self, test_client, mock_session):
        print("Testing upload file..")
        data = open(f"{hash(self.session_id)}/data_uploaded/data/unlabeled.csv", "rb")
        file = {"file": ("predict", data, "multipart/form-data")}
        response = self.client.post("/uploadfile/", files=file)
        assert response.json() == {"filename": "unlabeled.txt", "path": f"{hash(self.session_id)}/data_uploaded/unlabeled/unlabeled.txt"}
        assert response.status_code == 200

    def test_prediction(self, test_client, mock_session, mock_submit_job, mock_check_job, mock_backend_update):
        print("Testing prediction..")
        response = self.client.get("/final/start_prediction", params={"check": False})
        assert response.json() == {"Prediction": "started"}
        assert response.status_code == 200

    def test_download_prediction(self, test_client, mock_session, mock_results):
        print("Testing download predict..")
        data = {
            'label': [0, 1, 0, 1, 1],
            'text': [
                "I'm writing this review to give you a heads up before you see this Doctor.",
                "I don't know what Dr. Goldberg was like before moving to Arizona",
                "Been going to Dr. Goldberg for over 10 years.",
                "I am having a good time here.",
                "I am having a bad time here.",
            ]
        }
        directory_path = f"{hash(self.session_id)}/output"
        os.makedirs(directory_path, exist_ok=True)
        predictions_file = Path(f"{hash(self.session_id)}/output/predictions.csv")
        df = pd.DataFrame(data)
        df.to_csv(predictions_file, index=False)
        response = self.client.get("/download_prediction")
        assert response.status_code == 200

    def test_label_distribution(self, test_client, setting, mock_session):
        print("Testing label distribution")
        # Call the label_distribution function and check the response
        response = self.client.post("/label-distribution")
        assert response.status_code == 200
        assert exists("static/chart_prediction.png")
        assert response.json() == {"message": "Label distribution chart created successfully."}

    @pytest.fixture
    def mock_bash_cmd(self, mocker):
        mocker.patch('app.petGui.bash_cmd', return_value=(b"", b""))
        mocker.patch('app.controller.templating.bash_cmd', return_value=(b"", b""))


    @pytest.fixture
    def mock_backend_create(self, mocker):
        mocker.patch("fastapi_sessions.backends.implementations.in_memory_backend.InMemoryBackend.create",
                     return_value=InMemoryBackendMock.create)


    @pytest.fixture
    def mock_backend_update(self, mocker):
        mocker.patch("fastapi_sessions.backends.implementations.in_memory_backend.InMemoryBackend.update",
                     return_value=InMemoryBackendMock.update)

    def test_abort_job(self, test_client, mock_session, mock_bash_cmd, mock_backend_update):
        print("Testing abort job..")
        response = self.client.get("/abort_job", params={"final": False})
        assert response.json() == {"Status": "Cleaned"}
        assert response.status_code == 200

    def test_clean(self, test_client, mock_session, mock_bash_cmd, mock_backend_update):
        print("Testing clean..")
        response = self.client.get("/clean", params={"logout": False, "ssh": "sshpass"})
        assert response.status_code == 200
        assert response.json() == {"Status": "Cleaned"}

    def test_logout(self, test_client, mock_session, mock_bash_cmd, mock_backend_update):
        print("Testing logout..")
        response = self.client.get("/logout")
        assert response.json() == {"Logout": "successful"}


