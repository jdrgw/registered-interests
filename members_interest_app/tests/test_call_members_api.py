import os
import json
from django.test import TestCase
from django.conf import settings
from unittest.mock import patch
import responses
from members_interest_app.utils.call_members_api import fetch_members_data

class FetchDataTestCase(TestCase):

    @responses.activate
    @patch('time.sleep', return_value=None)  # Patch time.sleep to be a no-op
    @patch('members_interest_app.utils.call_members_api.range', return_value=range(0, 10))
    def test_fetch_members_data(self, mock_range, mock_sleep):
        # Prepare mock responses
        sample_response = {
            "key1": "value1",
            "key2": "value2"
        }
        for i in range(0, 10):  # testing with 10 mock requests
            responses.add(responses.GET, f'https://members-api.parliament.uk/api/Members/{i}',
                          json=sample_response, status=200)

        # Patch the file path to use a test-specific filename
        test_file_name = "test_members_of_parliament_2024_02_30.json"
        test_file_path = os.path.join(settings.BASE_DIR, 'data', 'members_data', 'raw_data', test_file_name)

        # Ensure the directory is clean before running the test
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

        with patch('members_interest_app.utils.call_members_api.os.path.join', return_value=test_file_path):
            fetch_members_data()

        # Debug statement to check the path
        print(f"Checking for file at path: {test_file_path}")

        # Check if the JSON file was created
        file_exists = os.path.exists(test_file_path)
        self.assertTrue(file_exists, f"The JSON file was not created at {test_file_path}")

        if file_exists:
            # Check the content of the JSON file
            with open(test_file_path, 'r') as f:
                content = json.load(f)

            # Debug statement to print the content read from the file
            print(f"Content read from {test_file_path}: {content}")

            # Ensure the content is as expected (ignoring order)
            expected_content = [{
                "key1": "value1",
                "key2": "value2",
                "status_code": 200,
                "searched_index": i
            } for i in range(0, 10)]

            print("expected_content",expected_content)
            
            # Debug statement to print the expected content
            # print(f"Expected content: {expected_content}")

            # Ensure both lists contain the same items, ignoring order
            self.assertCountEqual(content, expected_content)

            # Clean up by removing the created file after the test
            os.remove(test_file_path)

