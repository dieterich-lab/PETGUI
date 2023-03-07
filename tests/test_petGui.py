import io
import sys

from fastapi.testclient import TestClient
from app.petGui import app
from app.petGui import train
import pytest
import tempfile
import os
import json
import unittest
import shutil
from io import BytesIO
from fastapi import UploadFile
from unittest.mock import MagicMock, patch

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
        assert f"{response.next_request}" == f"{self.client.get('/logging', follow_redirects=False).request}"
        assert exists("logging.txt")
        assert exists(f"Pet/data_uploaded/{file['file'][0]}")

    def test_upload_data(self,setting):
        directory = "./Pet/data_uploaded/yelp_review_polarity_csv"

        expected_files = ["train.csv", "test.csv", "readme.txt"]

        # Check if the directory exists
        assert os.path.isdir(directory), f"Directory {directory} does not exist"

        # Check if the expected files exist in the directory
        for file_name in expected_files:
            file_path = os.path.join(directory, file_name)
            assert os.path.isdir(file_path), f"Directory {directory} does not exist"

    def test_save_dict_to_json_file(self,setting):
        with open(self.file_path, 'w') as file:
            json.dump(self.metadata, file)
        assert os.path.exists(self.file_path)
        with open(self.file_path, 'r') as file:
            loaded_dict = json.load(file)
        assert loaded_dict == self.metadata


    # def test_run(self, setting):
    #     response = self.client.get("/run", follow_redirects=False)
    #     assert response.status_code == 303
    #     assert f"{response.next_request}" == f"{self.client.get('/logging', follow_redirects=False).request}"

    def test_logging(self,setting):
        response = self.client.get("/logging")
        assert response.status_code == 200
        assert response.template.name == "next.html"

    # def test_logging(self, setting):
    #     response = self.client.get("/logging")
    #     assert response.status_code == 200
    #     assert exists("data.json")
    #     assert exists("output")
    #     assert exists("templates/run.html")
    #     assert exists("templates/results.html")
    #     assert b"PET done!" in response.content

    # def test_read_log(self,setting):
    #     log_content = """This is line 1.
    #     Creating an object.
    #     This is line 3.
    #     Saving the object.
    #     Starting evaluation.
    #     This is line 6.
    #     Training Complete.
    #     This is line 8.
    #     """
    #     with tempfile.NamedTemporaryFile(mode="w", delete=False) as log_file:
    #         log_file.write(log_content)
    #         log_file.flush()
    #         last_pos_file = log_file.name + ".pos"
    #         with open(last_pos_file, "w") as pos_file:
    #             pos_file.write("0")
    #         response = self.client.get("/log")
    #         assert response.status_code == 200
    #         assert response.json() == {"log": [
    #             "Creating an object.",
    #             "Saving the object.",
    #             "Starting evaluation.",
    #             "Training Complete."
    #         ]}
    #         with open(last_pos_file, "r") as pos_file:
    #             assert int(pos_file.read()) == len(log_content)
    #     os.unlink(log_file.name)
    #     os.unlink(last_pos_file)

    # def test_results(self, setting):
    #     response = self.client.get("/results")
    #     assert response.status_code == 200
    #     assert exists("results.json")

    def tearDown(self,setting):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def test_download(self,setting):
        # Generate a test dictionary
        test_dict = {
            "p0-i0": {"acc": 0.5},
            "p1-i1": {"acc": 0.8},
            "p2-i2": {"acc": 0.9},
        }

        # Write the test dictionary to a JSON file
        with open("results.json", "w") as f:
            json.dump(test_dict, f)

        # Make a GET request to the /download endpoint
        response = self.client.get("/download")

        # Check that the response status code is 200 OK
        assert response.status_code == 200

        # Check that the content type of the response is "application/json"
        assert response.headers["content-type"] == "application/json"

        # Check that the response body is not empty
        assert response.content

        # Decode the response content to a dictionary
        response_dict = json.loads(response.content)

        # Check that the response dictionary matches the test dictionary
        assert response_dict == test_dict

    def test_cleanup(self, setting):
        response = self.client.get("/cleanup")
        assert response.status_code == 200
        paths = ["results.json", "data.json", "output", "Pet/data_uploaded", "templates/run.html"]
        for p in paths:
            assert not exists(p)

    # @patch("builtins.open")
    # @patch("builtins.json.load")
    # @patch("app.custom_task_processor.report")
    # @patch("app.custom_task_pvp.report")
    # @patch("app.custom_task_metric.report")
    # @patch("app.train")
    # def test_kickoff(self,setting,train_mock, metric_report_mock, pvp_report_mock, task_report_mock, json_load_mock, open_mock):
    #     # Prepare test data
    #     json_load_mock.return_value = self.metadata
    #
    #     # Call the API
    #     response = client.get("/logging/start_train")
    #
    #     # Verify the response status code is 200
    #     assert response.status_code == 200
    #
    #     # Verify the mock function calls
    #     json_load_mock.assert_called_once_with(open_mock().__enter__().name, "r")
    #     task_report_mock.assert_called_once()
    #     pvp_report_mock.assert_called_once()
    #     metric_report_mock.assert_called_once()
    #     train_mock.assert_called_once_with(data["file"], list(
    #         range(len(data.keys())) - 3))  # Exclude "file", "model_para", and "label" keys from template_cnt

    def test_get_final_template(self,setting):
        response = self.client.get("/final")
        assert response.status_code == 200


    def test_create_upload_file(self,setting):
        # make sure upload folder exists and is empty
        test_file_content = b"test file content"
        test_file = UploadFile(filename="test.csv", file=BytesIO(test_file_content))
        upload_folder = "./Pet/data_uploaded/unlabeled"
        os.makedirs(upload_folder, exist_ok=True)
        shutil.rmtree(upload_folder)
        os.makedirs(upload_folder, exist_ok=True)

        # call the API endpoint with the test file
        response = self.client.post("/uploadfile/", files={"file": test_file})

        # check that the API returned the expected response
        assert response.status_code == 200
        assert response.json() == {"filename": "test.csv", "path": os.path.join(upload_folder, "test.csv")}

        # check that the file was actually saved to the upload folder
        with open(os.path.join(upload_folder, "test.csv"), "rb") as f:
            assert f.read() == test_file_content







