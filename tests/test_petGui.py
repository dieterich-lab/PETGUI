import json
import os
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.petGui import app, get_session_service, User
import pytest
from fastapi.responses import RedirectResponse, FileResponse
from unittest.mock import MagicMock
from app.dto.session import SessionData
from app.services.session import SessionService, cookie, verifier
import io
from os.path import exists
from app.controller.templating import router

class TestServer:
    session_id = uuid4()
    session_data = SessionData(
        username="username",
        remote_loc="remote_location",
        remote_loc_pet="remote_location_pet",
        cluster_name="cluster_name",
        last_pos_file="last_pos_file",
        log_file="log_file"
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
    def mock_session(self):
        self.mock_get_session_service = SessionService(self.session_data, self.session_id)
        self.mock_verifier = self.session_data        # Not a necessity
        self.mock_cookie = "long-fake-uuid"       # Not a necessity

        app.dependency_overrides[cookie] = lambda: self.mock_cookie       # Not a necessity
        app.dependency_overrides[get_session_service] = lambda: self.mock_get_session_service
        app.dependency_overrides[verifier] = lambda: self.mock_verifier       # Not a necessity
        app.state = User()      # Not a necessity
        app.state.session = self.mock_get_session_service
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

    def test_login(self, test_client):
        print("Testing login..")
        response = self.client.post("/login", data=self.data)
        assert response.status_code == 200

    def test_whoami(self, test_client, mock_session):
        print("Testing whoami..")
        response = self.client.get("/whoami")
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
        # assert exists("logging.txt")

    @pytest.fixture
    def mock_results(self):
        with open(f"{hash(self.session_id)}/results.json", "w") as f:
            json.dump({"results": "good"}, f)
        yield FileResponse(f"{hash(self.session_id)}")

    def test_results(self, test_client, mock_session, mock_results):
        print("Testing results..")
        response = self.client.get("/download")
        assert exists(f"{hash(self.session_id)}/results.json")
        assert response.status_code == 200
