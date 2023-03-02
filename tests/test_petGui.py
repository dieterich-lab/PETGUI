import io
import sys

from fastapi.testclient import TestClient
from app.petGui import app
import pytest
import tempfile
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
        self.file_path = "data.json" #
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

    def test_upload_data(self,setting):
        directory = "data/yelp_review_polarity_csv"

        expected_files = ["train.csv", "test.csv", "readme.txt"]

        # Check if the directory exists
        self.assertTrue(os.path.isdir(directory), f"Directory {directory} does not exist")

        # Check if the expected files exist in the directory
        for file_name in expected_files:
            file_path = os.path.join(directory, file_name)
            self.assertTrue(os.path.isfile(file_path), f"File {file_path} does not exist")

    def test_save_dict_to_json_file(self,setting):
        with open(file_path, 'w') as file:
            json.dump(dict_data, file)

        self.assertTrue(os.path.exists(self.file_path))

        with open(self.file_path, 'r') as file:
            loaded_dict = json.load(file)
        self.assertDictEqual(loaded_dict, self.metadata)

    def test_run(self, setting):
        response = self.client.get("/run", follow_redirects=False)
        assert response.status_code == 303
        assert f"{response.next_request}" == f"{self.client.get('/logging', follow_redirects=False).request}"

    def test_logging(self,setting):
        request = Request({"type": "http", "method": "GET", "url": "http://testserver/logging"})
        response = client.get("/logging", headers={"accept": "text/html"})
        assert response.status_code == 200
        assert b"Next Page" in response.content
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert response.template.name == "next.html"
        assert response.template.context["request"] == request

    # def test_logging(self, setting):
    #     response = self.client.get("/logging")
    #     assert response.status_code == 200
    #     assert exists("data.json")
    #     assert exists("output")
    #     assert exists("templates/run.html")
    #     assert exists("templates/results.html")
    #     assert b"PET done!" in response.content

    def test_read_log(self,setting):
        log_content = """This is line 1.
        Creating an object.
        This is line 3.
        Saving the object.
        Starting evaluation.
        This is line 6.
        Training Complete.
        This is line 8.
        """
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as log_file:
            log_file.write(log_content)
            log_file.flush()
            last_pos_file = log_file.name + ".pos"
            with open(last_pos_file, "w") as pos_file:
                pos_file.write("0")
            response = client.get("/log")
            assert response.status_code == 200
            assert response.json() == {"log": [
                "Creating an object.",
                "Saving the object.",
                "Starting evaluation.",
                "Training Complete."
            ]}
            with open(last_pos_file, "r") as pos_file:
                assert int(pos_file.read()) == len(log_content)
        os.unlink(log_file.name)
        os.unlink(last_pos_file)

    def test_results(self, setting):
        response = self.client.get("/results")
        assert response.status_code == 200
        assert exists("results.json")

    def tearDown(self,setting):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            
    def test_download(self, setting):
        response = self.client.get("/download")
        assert b'pre-rec-f1-supp' in response.content

    def test_cleanup(self, setting):
        response = self.client.get("/cleanup")
        assert response.status_code == 200
        paths = ["results.json", "data.json", "output", "Pet/data_uploaded", "templates/run.html"]
        for p in paths:
            assert not exists(p)

