import io
import sys
from fastapi.testclient import TestClient
from app.petGui import app
from fastapi import Depends, Cookie
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters

#from app.petGui import train
import pytest
import os
import tempfile
import os
import json
import unittest
import shutil
from io import BytesIO
import pandas as pd
import unittest.mock as mock
from fastapi import UploadFile
from unittest.mock import MagicMock, patch
from os.path import exists
from app.petGui import results
from transformers import BertTokenizer
import os
import tempfile
import asyncio
from fastapi import HTTPException, FastAPI, Response, Depends
from uuid import UUID, uuid4
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
import uuid
from unittest.mock import MagicMock


class TestServer:
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
        self.mock_cookie = MagicMock()
        self.mock_cookie.return_value = uuid.uuid4()
        self.client = TestClient(app)
        #override dependency
        app.dependency_overrides[cookie] = self.mock_cookie


        # self.mock_cookie = SessionCookie(
        #     cookie_name="cookie",
        #     identifier="general_verifier",
        #     auto_error=True,
        #     secret_key="DONOTUSE",
        #     cookie_params=cookie_params,
        # ).new_uuid()
        # session_id = uuid.uuid4()
        # session_data = SessionData(username="testuser", remote_loc="testloc", remote_loc_pet="testpet")
        # backend.save(session_id, session_data)
        # cookie_value = cookie.create(session_id)
        # headers = {"Cookie": f"cookie={cookie_value}"}


        #self.client._cookie_jar.update_cookies({"cookie_name": "valid_cookie"})
        #self.client.cookies.set("cookie", "valid_cookie")
        # yield
        # self.client.close()

    # @mock.patch('app.login.authenticate_ldap')
    # @mock.patch('app.login.create_session')
    # async def test_login(self, mock_create_session, mock_authenticate_ldap):
    #     mock_authenticate_ldap.return_value = True
    #     mock_create_session.return_value = None
    #     response = await self.client.post("/login", data={"username": "testuser", "password": "testpass"})
    #     assert response.status_code == 303
    #     assert response.url == "/homepage"
    #     assert "testuser" in os.environ
    #     assert os.environ["testuser"] == "testpass"
    # @patch('__main__.authenticate', return_value=True)
    # def test_login_successful(self, mock_authenticate):
    #     response = client.post("/login", json={"username": "johndoe", "password": "password123"})
    #     assert response.status_code == 200
    #     assert response.json() == {"message": "Login successful"}
    #
    # @patch('__main__.authenticate', return_value=False)
    # def test_login_failed(self, mock_authenticate):
    #     response = self.client.post("/login", json={"username": "johndoe", "password": "incorrect_password"})
    #     assert response.status_code == 200
    #     assert response.json() == {"message": "Login successful"}
    # def mock_cookie(self):
    #     def _mock_cookie(self):
    #         return "valid_cookie"
    #     return _mock_cookie

    # def session_cookie(self):
    #     cookie_params = {
    #         "httponly": True,
    #         "samesite": "lax",
    #         "secure": True,
    #     }
    #     return SessionCookie(
    #         cookie_name="cookie",
    #         identifier="general_verifier",
    #         auto_error=True,
    #         secret_key="DONOTUSE",
    #         cookie_params=cookie_params,
    #     )

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
        assert exists(f"data_uploaded/{file['file'][0]}")


    # def test_upload_data(self,setting):
    #     directory = "data/yelp_review_polarity_csv"


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
        #setting.client.cookies.set('cookie', setting.mock_cookie)
        assert response.status_code == 200 # Check if it is
        assert exists("data.json")
        assert exists("output")
        assert exists("templates/next.html")
        assert exists("logging.txt")


    def test_results(self, setting):
        response = self.client.get("/results")
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

    def test_predictions(self,setting):
        # Define the path to the test CSV file
        test_csv_path = "Pet/data_uploaded/yelp_review_polarity_csv/unlabeled.csv"
        # Create a test dataframe with some sample text
        test_df = pd.DataFrame({'text': ['This is a test review', 'Another test review']})
        # Save the test dataframe to a CSV file
        test_df.to_csv(test_csv_path, index=False)
        # Load the CSV file using the code we want to test
        tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        model = BertForSequenceClassification.from_pretrained('bert-base-uncased')
        df = pd.read_csv(test_csv_path, header=None, names=['label', 'text'])
        input_ids = []
        attention_masks = []
        for text in df['text']:
            encoded_dict = tokenizer.encode_plus(
                text,
                add_special_tokens=True,
                max_length=64,
                pad_to_max_length=True,
                return_attention_mask=True,
                return_tensors='pt'
            )
            input_ids.append(encoded_dict['input_ids'])
            attention_masks.append(encoded_dict['attention_mask'])
        input_ids = torch.cat(input_ids, dim=0)
        attention_masks = torch.cat(attention_masks, dim=0)
        with torch.no_grad():
            outputs = model(input_ids, attention_mask=attention_masks)
        logits = outputs[0]
        predictions = torch.argmax(logits, dim=1)
        df['label'] = predictions
        df.to_csv('test_predictions.csv', index=False)
        # Load the test predictions CSV file
        test_predictions_df = pd.read_csv('test_predictions.csv')
        # Verify that the predicted labels are integers between 0 and 1
        for label in test_predictions_df['label']:
            assert isinstance(label, int)
            assert label == 0 or label == 1

        # Test the API endpoint

        response = self.client.get("/final/start_prediction")
        assert response.status_code == 200
        assert response.json() == {"message": "Predictions generated successfully."}

    def test_results(self):
        # Mock the os.walk and open functions to simulate the directory structure and results.json content
        with mock.patch('os.walk') as mock_walk, mock.patch('builtins.open', mock.mock_open(read_data=json.dumps({
            "test_set_after_training": {
                "acc": 0.9,
                "pre-rec-f1-supp": [
                    [0.8, 0.7, 0.75, 100],
                    [0.9, 0.8, 0.85, 150]
                ]
            }
        }))):
            mock_walk.return_value = ("output/", ["final", "pattern-1"], [])
            mock_walk.side_effect = [
                ("output/final/", [], []),
                ("output/pattern-1/", ["iteration-1"], []),
                ("output/pattern-1/iteration-1", [], ["results.json"]),
            ]

            # Call the results function
            result = results()

            # Define the expected output
            expected_scores = {
                "Final": {
                    "acc": 0.9,
                    "pre-rec-f1-supp": [
                        "Label: 0 pre: 0.8, rec: 0.7, f1: 0.75, supp: 100",
                        "Label: 1 pre: 0.9, rec: 0.8, f1: 0.85, supp: 150"
                    ]
                },
                "Pattern-1 Iteration 1": {
                    "acc": 0.9,
                    "pre-rec-f1-supp": [
                        "Label: 0 pre: 0.8, rec: 0.7, f1: 0.75, supp: 100",
                        "Label: 1 pre: 0.9, rec: 0.8, f1: 0.85, supp: 150"
                    ]
                }
            }

            # Assert that the result matches the expected output
            assert result == expected_scores


    def test_create_upload_file(self):
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_file.seek(0)

            # Create a test UploadFile object
            test_upload_file = UploadFile(temp_file.name, file=temp_file)

            # Call the create_upload_file function
            result = asyncio.run(create_upload_file(file=test_upload_file))

            # Define the expected output
            expected_result = {
                "filename": temp_file.name,
                "path": os.path.join("./data_uploaded/unlabeled", temp_file.name)
            }

            # Assert that the result matches the expected output
            assert result == expected_result

            # Clean up the temporary file
            os.remove(temp_file.name)






