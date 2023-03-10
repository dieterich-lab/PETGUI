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
            "file": "yelp_review_polarity_csv",
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

    # def test_upload_data(self,setting):
    #     directory = "Pet/data_uploaded/yelp_review_polarity_csv"
    #
    #     expected_files = ["train.csv", "test.csv", "readme.txt"]
    #
    #     # Check if the directory exists
    #     assert os.path.isdir(directory), f"Directory {directory} does not exist"
    #
    #     # Check if the expected files exist in the directory
    #     for file_name in expected_files:
    #         file_path = os.path.join(directory, file_name)
    #         assert os.path.isdir(file_path), f"Directory {directory} does not exist"

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


    def test_read_log(self,setting):
        # Clean up test files
        log_file =  "logging.txt"
        last_pos_file = "last_pos.txt"
        # if os.path.exists(log_file):
        #     os.remove(log_file)
        # if os.path.exists(last_pos_file):
        #     os.remove(last_pos_file)

        # Prepare test data
        with open(log_file, "w") as f:
            f.write("Creating object A\n")
            f.write("Training Complete\n")
            f.write("Creating object B\n")
            f.write("Saving model\n")
            f.write("Starting evaluation\n")
            f.write("Returning result\n")

        # Initialize last_pos to the value stored in last_pos.txt, or 0 if the file does not exist
        if os.path.exists(last_pos_file):
            with open(last_pos_file, "r") as file:
                last_pos = int(file.read())
        else:
            last_pos = 0
        # Call the endpoint


        response = self.client.get("/log")


        # Check the response
        assert response.status_code == 200

        expected_output = {
            "log": [
                "Creating object A",
                "Training Complete",
                "Creating object B",
                "Saving model",
                "Starting evaluation",
                "Returning result",
            ]
        }


        assert response.json() == expected_output

        # Check that last_pos has been updated correctly
        with open(log_file, "r") as file:
            file.seek(last_pos)
            lines = file.readlines()
            last_pos = file.tell()
        with open(last_pos_file, "w") as file:
            file.write(str(last_pos))

        #assert last_pos == len(expected_output["log"][-1]) + 1

        # Clean up test files
        os.remove(log_file)
        os.remove(last_pos_file)

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


    def test_kickoff(self,setting):
        # Prepare test data

        # Call the API
        with open(self.file_path,"w") as file:
            json.dump(self.metadata, file)
        response = self.client.get("/logging/start_train")

        # Verify the response status code is 200
        assert response.status_code == 200

        # Verify the mock function calls
        # json_load_mock.assert_called_once_with(open_mock().__enter__().name, "r")
        # task_report_mock.assert_called_once()
        # pvp_report_mock.assert_called_once()
        # metric_report_mock.assert_called_once()
        # train_mock.assert_called_once_with(data["file"], list(
        #     range(len(data.keys())) - 3))  # Exclude "file", "model_para", and "label" keys from template_cnt

    def test_get_final_template(self,setting):
        response = self.client.get("/final")
        assert response.status_code == 200


    # def test_create_upload_file(self,setting):
    #     # make sure upload folder exists and is empty
    #     test_file_content = b"test file content"
    #     test_file = UploadFile(filename="test.csv", file=BytesIO(test_file_content))
    #     upload_folder = "./Pet/data_uploaded/unlabeled"
    #     os.makedirs(upload_folder, exist_ok=True)
    #     shutil.rmtree(upload_folder)
    #     os.makedirs(upload_folder, exist_ok=True)
    #
    #     # call the API endpoint with the test file
    #     response = self.client.post("/uploadfile/", files={"file": test_file})
    #
    #     # check that the API returned the expected response
    #     assert response.status_code == 200
    #     assert response.json() == {"filename": "test.csv", "path": os.path.join(upload_folder, "test.csv")}
    #
    #     # check that the file was actually saved to the upload folder
    #     with open(os.path.join(upload_folder, "test.csv"), "rb") as f:
    #         assert f.read() == test_file_content






