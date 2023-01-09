import io
from fastapi.testclient import TestClient
from app.petgui import app
import pytest
import pathlib
import shutil
from os.path import exists, isfile, isdir

class TestServer:
    @pytest.fixture()
    def setting(self):
        self.metadata = {
            "sample": "1",
            "label": "0",
            "templates": "It was_.",
            "one": "bad",
            "two": "nice",
            "model_para": "gbert-base"
        }
        self.client = TestClient(app)

    @pytest.fixture(autouse=False)
    def cleanup_files(self):
        self.paths = ["data.json", "output", "Pet/data_uploaded"]
        for path in self.paths:
            file_path = pathlib.Path(path)
            if isfile(path):
                file_path.unlink()
            elif isdir(path):
                shutil.rmtree(path)

    def test_home(self, setting):
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Hello":"World"}

    def test_basic(self, setting, capsys):
        with open("data/yelp_review_polarity_csv.tar.gz", "rb") as f:
            data = io.BytesIO(f.read())

        file = {"file": ("yelp_review_polarity_csv", data, "multipart/form-data")}
        response = self.client.post(
            "/basic",
            data=self.metadata,
            files=file,
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert f"{response.next_request}" == f"{self.client.get('/run', follow_redirects=False).request}"
        captured = capsys.readouterr()
        sample = self.metadata["sample"]
        label = self.metadata["label"]
        templates = self.metadata["templates"]
        one = self.metadata["one"]
        two = self.metadata["two"]
        model_para = self.metadata["model_para"]
        assert captured.out == f"sample:{sample}\nlabel:{label}\ntemplates:{templates}\n1:{one}\n2:{two}\nmodel_para:{model_para}\n"

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

    def test_cleanup(self, cleanup_files):
        for path in self.paths:
            assert not exists(path)
