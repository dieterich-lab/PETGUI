import io
import sys

from fastapi.testclient import TestClient
from app.petGui import app
import pytest
from os.path import exists

class TestServer:
    @pytest.fixture()
    def setting(self):
        self.metadata = {
            "sample": "1",
            "label": "0",
            "template_0": "It was _ .",
            "origin_0": "1",
            "mapping_0": "bad",
            "origin_1": "2",
            "mapping_1": "good",
            "model_para": "gbert-base"
        }
        self.client = TestClient(app)

    def test_home(self, setting):
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello":"World"}

    def test_basic(self, setting):
        with open("data/yelp_review_polarity_csv.tar.gz", "rb") as f:
            data = io.BytesIO(f.read())

        file = {"file": ("yelp_review_polarity_csv", data, "multipart/form-data")}
        prep = self.client.get("/basic")
        assert prep.status_code == 200

        response = self.client.post(
            "/basic",
            data=self.metadata,
            files=file,
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert f"{response.next_request}" == f"{self.client.get('/run', follow_redirects=False).request}"
        assert exists("logging.txt")
        assert exists(f"Pet/data_uploaded/{file['file'][0]}")

    def test_run(self, setting):
        response = self.client.get("/run", follow_redirects=False)
        assert response.status_code == 303
        assert f"{response.next_request}" == f"{self.client.get('/logging', follow_redirects=False).request}"

    def test_logging(self, setting):
        response = self.client.get("/logging")
        assert response.status_code == 200
        assert exists("data.json")
        assert exists("output")
        assert exists("templates/run.html")
        assert exists("templates/results.html")
        assert b"PET done!" in response.content

    def test_results(self, setting):
        response = self.client.get("/results")
        assert response.status_code == 200
        assert exists("results.json")

    def test_download(self, setting):
        response = self.client.get("/download")
        assert b'pre-rec-f1-supp' in response.content

    def test_cleanup(self, setting):
        response = self.client.get("/cleanup")
        assert response.status_code == 200
        paths = ["results.json", "data.json", "output", "Pet/data_uploaded", "templates/run.html"]
        for p in paths:
            assert not exists(p)
