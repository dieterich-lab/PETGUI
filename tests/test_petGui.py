import json
import os
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.petGui import app, get_session_service, User
import pytest
from fastapi.responses import FileResponse
from app.dto.session import SessionData, cookie, verifier
from app.services.session import SessionService
import io
from os.path import exists
import pandas as pd
import matplotlib.pyplot as plt
from app.controller.templating import router


class TestServer:
    session_id = uuid4()
    session_data = SessionData(
        username="username",
        remote_loc="remote_location",
        remote_loc_pet="remote_location_pet",
        cluster_name="cluster_name",
        last_pos_file=f"{hash(session_id)}/last_pos_file.txt",
        log_file=f"{hash(session_id)}/log_file.txt"
    )
    data = {"username": "user", "password": "pass"}
    app = FastAPI()

    @pytest.fixture()
    def setting(self):
        self.metadata = {
            "file": "yelp_review_polarity_csv",
            "sample": "1",
            "label": "0",
            "template_0": "It was _ .",
            "template_1": "All in all _ .",
            "template_2": "Just _ .",
            "origin_0": "1",
            "mapping_0": "bad",
            "origin_1": "2",
            "mapping_1": "good",
            "model_para": "gbert-base"
        }
        self.file_path = "data.json"
        yield self.metadata, self.file_path

    @pytest.fixture
    def mock_session(self, mocker):
        self.mock_get_session_service = SessionService(self.session_data, self.session_id)
        self.mock_verifier = self.session_data        # Not a necessity
        self.mock_cookie = "long-fake-uuid"       # Not a necessity

        app.dependency_overrides[cookie] = lambda: self.mock_cookie       # Not a necessity
        app.dependency_overrides[get_session_service] = lambda: self.mock_get_session_service
        app.dependency_overrides[verifier] = lambda: self.mock_verifier       # Not a necessity
        app.state = User()      # Not a necessity
        app.state.session = self.mock_get_session_service
        mocker.patch("app.petGui.create_session", return_value=app.state.session)
        yield app.state.session


    @pytest.fixture
    def test_client(self):
        self.app.include_router(router)        # Not a necessity
        self.client = TestClient(app)
        yield self.client

    def test_home(self, test_client):
        print("Testing app start..")
        response = self.client.get("/")
        assert response.status_code == 200

    @pytest.fixture
    def mock_user(self, mocker):
        mocker.patch("app.services.ldap.LdapService.authenticate_ldap", return_value=True)  # Return user authentication

    def test_login(self, test_client, mock_user, mock_session):
        print("Testing login..")
        response = self.client.post("/login", data=self.data)
        assert response.status_code == 200

    def test_whoami(self, test_client, mock_session):
        print("Testing whoami..")
        response = self.client.get("/whoami")
        print(response.content)
        assert response.status_code == 200

    def test_basic(self, test_client, setting, mock_session):
        print("Testing homepage..")
        with open("data/yelp_review_polarity_csv.tar.gz", "rb") as f:
            data = io.BytesIO(f.read())
        file = {"file": ("yelp_review_polarity_csv", data, "multipart/form-data")}
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
        assert exists(f"{hash(self.session_id)}/data_uploaded/{file['file'][0]}")
        assert exists(f"{self.session_data.log_file}")

    def test_logging(self, test_client, mock_session):
        print("Testing logging..")
        response = self.client.get("/logging")
        assert response.status_code == 200
        assert exists(f"{hash(self.session_id)}/data.json")
        # assert exists("output")
        assert exists("templates/next.html")


    @pytest.fixture
    def mock_submit_job(self, mocker):
        mocker.patch("app.petGui.submit_job", return_value=1234)  # Return job-id

    @pytest.fixture
    def mock_check_job(self, mocker):
        mocker.patch("app.petGui.check_job_status", return_value="CD")  # Return job-status

    def test_logging_train(self, test_client, mock_session, mock_submit_job, mock_check_job):
        print("Testing training..")
        response = self.client.get("/logging/start_train")
        assert response.status_code == 200

    @pytest.fixture
    def mock_results(self, mock_session):
        with open(f"{hash(self.session_id)}/results.json", "w") as f:
            json.dump({"results": "good"}, f)
        yield FileResponse(f"{hash(self.session_id)}")

    def test_results(self, test_client, mock_session, mock_results):
        print("Testing results..")
        response = self.client.get("/download")
        assert exists(f"{hash(self.session_id)}/results.json")
        assert response.status_code == 200

    @pytest.fixture
    def test_label_distribution(self, mocker, test_client, setting, mock_session):
        # Mock the get_session_service dependency
        # Create a mock dataframe with known label values
        df = pd.DataFrame({"label": ["A", "B", "C", "A", "B", "C", "A", "B", "C", "A", "B", "C"]})
        predictions_file = f"{hash(self.session_id)}/data_uploaded/predictions.csv"
        df.to_csv(predictions_file)

        # Mock the matplotlib plot and save it to a temporary file
        fig, ax = plt.subplots()
        ax.bar(["A", "B", "C"], [4, 4, 4])
        ax.set_title("Label Counts")
        ax.set_xlabel("Label")
        ax.set_ylabel("Number of Examples")
        table_data = [["Label", "Text"], ["A", "mock text..."], ["B", "mock text..."], ["C", "mock text..."]]
        table = ax.table(cellText=table_data, loc="bottom", cellLoc="left", bbox=[0, -0.8, 1, 0.5])
        table.auto_set_column_width(col=list(range(2)))
        chart_file = "chart_prediction.png"
        plt.savefig(chart_file, dpi=100)

        # Call the label_distribution function and check the response
        client = TestClient(app)
        response = client.post("/label-distribution")
        assert response.status_code == 200
        assert response.json() == {"message": "Label distribution chart created successfully."}
        assert predictions_file.exists()
        assert chart_file.exists()

    @pytest.fixture
    def test_extract_file(self,mocker, test_client, setting, mock_session):

       # Create a mock dataframe with known label values
        df = pd.DataFrame({"label": ["A", "B", "C", "A", "B", "C", "A", "B", "C", "A", "B", "C"]})
        train_file = f"{hash(self.session_id)}/data_uploaded/train.csv"
        test_file =  f"{hash(self.session_id)}/data_uploaded/test.csv"
        df.to_csv(train_file, index=False)
        df.to_csv(test_file, index=False)

        # Mock the matplotlib plot and save it to a temporary file
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(7, 5))
        ax1.bar(["A", "B", "C"], [4, 4, 4], width=0.5)
        ax1.set_title("Train Label Distribution")
        ax1.set_xlabel("Label")
        ax1.set_ylabel("Count")
        ax2.bar(["A", "B", "C"], [4, 4, 4], width=0.5)
        ax2.set_title("Test Label Distribution")
        ax2.set_xlabel("Label")
        ax2.set_ylabel("Count")
        chart_file = "chart.png"
        plt.savefig(chart_file, dpi=100)

        # Call the extract_file function and check the response
        client = TestClient(app)
        with open(train_file, "rb") as f1, open(test_file, "rb") as f2:
            response = client.post("/extract-file", files={"file": ("data.tar.gz", f1), "file": ("data.tar.gz", f2)})
        assert response.status_code == 200
        assert response.json() == {"message": "File extracted successfully."}
        assert train_file.exists()
        assert test_file.exists()
        assert chart_file.exists()
