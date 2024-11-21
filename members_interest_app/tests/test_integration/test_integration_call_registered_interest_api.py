import tempfile
import os
import json
from unittest import TestCase
from unittest.mock import patch
from members_interest_app.utils.call_registered_interests import call_api_and_save_data


class TestIntegrationCallRegisteredInterestAPI(TestCase):
    # Patch database calls to limit API calls from 5k to 2, ensuring efficiency in this integration test
    @patch("members_interest_app.models.MemberOfParliament.objects.filter")
    def test_integration_call_api_and_append_data(self, mock_api_ids):
        """
        Test whether the functions calling registered interest API from parliament API
        produce expected results.
        """

        try:
            # Define the fake file data
            fake_file_data = {
                "value": [],
                "links": [
                    {"rel": "self", "href": "/Members/1/Interests", "method": "GET"}
                ],
            }

            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w+", encoding="utf-8", delete=False
            ) as f:
                temp_file_path = f.name
                print(temp_file_path)

                # Write initial JSON data to the temp file with separator
                json.dump(fake_file_data, f)
                f.write("\n\n\n")  # Separate JSON lines
                f.flush()

            # Simulate DB query returning `api_ids`
            mock_api_ids.return_value.order_by.return_value.values_list.return_value = [
                "1",
                "2",
            ]

            # Call the function that modifies the file
            result = call_api_and_save_data(temp_file_path)  # noqa: F841

            with open(temp_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

                # Ensure api_id 1 appears only once, as existing entries are skipped in API calls
                assert (
                    sum(1 for line in lines if '"href": "/Members/1/Interests"' in line)
                    == 1
                )

                # prove function adds object for member with api_id 2, doing so only once
                assert any('"href": "/Members/2/Interests"' in line for line in lines)
                assert (
                    sum(1 for line in lines if '"href": "/Members/2/Interests"' in line)
                    == 1
                )

        finally:
            # Delete the temporary file
            os.remove(temp_file_path)
