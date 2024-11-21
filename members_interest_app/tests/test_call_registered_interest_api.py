from unittest.mock import patch, mock_open, MagicMock
from members_interest_app.utils.call_registered_interests import (
    extract_api_ids_from_file,
    call_api_and_save_data,
)

from django.test import TestCase


class TestExtractApiIds(TestCase):
    @patch("builtins.open", new_callable=mock_open)
    def test_file_opened(self, mock_file):
        "Test whether file is opened"
        file_path = "some/file/path.json"
        result = extract_api_ids_from_file(file_path)  # noqa: F841

        assert mock_file.call_count == 1

    def test_succesful_extraction_of_api_ids(self):
        """
        extract_api_ids_from_file() function checks whether a file exists and if it does,
        then it processes the data and retrieves a set of api_ids.

        using fake data, this test will check whether that extraction process works
        on correctly formatted data
        """

        file_data = """
        {
            "value": [],
            "links": [
                {"rel": "self", "href": "/Members/1/Interests", "method": "GET"}
                ]
        }\n\n\n
        {
            "value": [],
            "links": [
                {"rel": "self", "href": "/Members/2/Interests", "method": "GET"}
                ]
        }
        """

        # Mock the open function to simulate the file content
        with patch("builtins.open", mock_open(read_data=file_data)):
            file_path = "some/file/path.json"
            extracted_ids = extract_api_ids_from_file(file_path)

        self.assertEqual(extracted_ids, set(["1", "2"]))

    @patch("builtins.print")
    def test_no_valid_links_array(self, mock_print):
        """
        Test if the function handles and prints a message when there is no valid 'links' array in the JSON object.
        """

        # Simulate JSON data with missing 'links' array or an invalid format for 'links'
        file_data = """
        {
            "value": [],
            "links": null
        }\n\n\n
        {
            "value": [],
            "links": "not_a_list"
        }\n\n\n
        {
            "value": [],
            "links": []
        }
        """

        # Mock the open function to simulate the file content
        with patch("builtins.open", mock_open(read_data=file_data)):
            file_path = "some/file/path.json"
            extract_api_ids_from_file(file_path)

        self.assertTrue(mock_print.called)
        mock_print.assert_any_call(
            "No valid 'links' array in object: {'value': [], 'links': None}"
        )
        mock_print.assert_any_call(
            "No valid 'links' array in object: {'value': [], 'links': 'not_a_list'}"
        )
        mock_print.assert_any_call(
            "No valid 'links' array in object: {'value': [], 'links': []}"
        )

    @patch("builtins.print")
    def test_no_capture_group(self, mock_print):
        """
        Test if the function handles the case when no capture group is found in the href URL.
        """

        # Simulate JSON with a link that doesn't match the regex
        file_data = """
        {
            "value": [],
            "links": [
                {"rel": "self", "href": "/OtherPath/1/NoMatch", "method": "GET"}
            ]
        }\n\n\n
        {
            "value": [],
            "links": [
                {"rel": "self", "href": "/OtherPath/2/NoMatch", "method": "GET"}
            ]
        }
        """

        # Mock the open function to simulate file content
        with patch("builtins.open", mock_open(read_data=file_data)):
            file_path = "some/file/path.json"
            extract_api_ids_from_file(file_path)

        self.assertTrue(mock_print.called)
        mock_print.assert_any_call(
            "no match for [{'rel': 'self', 'href': '/OtherPath/1/NoMatch', 'method': 'GET'}] when searching for in-file api_ids"
        )
        mock_print.assert_any_call(
            "no match for [{'rel': 'self', 'href': '/OtherPath/2/NoMatch', 'method': 'GET'}] when searching for in-file api_ids"
        )


class TestCallRegisteredInterests(TestCase):
    @patch("builtins.open", new_callable=mock_open)
    def test_file_opened(self, mock_file):
        "Test whether file is opened"
        result = call_api_and_save_data()  # noqa: F841

        assert mock_file.call_count == 2

    @patch("builtins.open", new_callable=mock_open)
    @patch(
        "members_interest_app.utils.call_registered_interests.extract_api_ids_from_file"
    )
    @patch("members_interest_app.utils.call_registered_interests.requests.Session.get")
    @patch("members_interest_app.models.MemberOfParliament.objects.filter")
    def test_append_new_data_to_file(
        self, mock_api_ids, mock_request, mock_extracted_ids, mock_write
    ):
        """
        Test the function that appends new data about MPs' registered interests to a JSON file by cross-referencing
        their 'api_id' values (unique identifiers from the parliament API) between the database and the file.

        The JSON file stores data about MPs's registered interests, with 'api_id's embedded within links.
        If data for an MP already exists in the file, the function skips making further API requests for that MP,
        to avoid duplicate data.

        The function works by:
        - Getting 'api_id's already stored in the database (via the `MemberOfParliament` class).
        - Taking a set of 'api_ids' passed to it from another function
        - If an 'api_id' in the file matches an 'api_id' in the database, no new data is fetched or appended.
        - If no match is found, a request is made to the parliament API, and the new data is appended to the file.

        This test ensures:
        - Only data (registered interests) about MPs not in the file is appended, preventing duplication, which
        also verifies the matching process
        """

        # simulate db query returning api_ids
        mock_api_ids.return_value.order_by.return_value.values_list.return_value = [
            "1",
            "2",
        ]
        db_api_ids = (
            mock_api_ids.return_value.order_by.return_value.values_list.return_value
        )

        # simulate extract_api_ids_from_file function, which is called by call_api_and_save_data function
        mock_extracted_ids.return_value = set(["1"])
        extracted_ids = mock_extracted_ids.return_value

        # simulate request and response
        mock_request.return_value.status_code = 200
        responses = [
            {
                "value": [],
                "links": [
                    {"rel": "self", "href": f"/Members/{i}/Interests", "method": "GET"}
                ],
            }
            for i in db_api_ids
            if str(i) not in extracted_ids
        ]
        mock_request.return_value.json = lambda: responses

        result = call_api_and_save_data()  # noqa: F841

        write_calls = [call[0][0] for call in mock_write().write.call_args_list]
        glued_write_calls = "".join(write_calls)

        mock_write().write.assert_called()

        for response in responses:
            expected_href = response["links"][0]["href"]
            assert expected_href in glued_write_calls

        for extracted_id in extracted_ids:
            assert f"/Members/{extracted_id}/Interests" not in glued_write_calls

        assert glued_write_calls.count("/Members/") == len(responses)

    @patch("members_interest_app.utils.call_registered_interests.time.sleep")
    @patch("builtins.print")
    @patch("builtins.open", new_callable=mock_open)
    @patch(
        "members_interest_app.utils.call_registered_interests.extract_api_ids_from_file"
    )
    @patch("members_interest_app.utils.call_registered_interests.requests.Session.get")
    @patch("members_interest_app.models.MemberOfParliament.objects.filter")
    def test_server_error(
        self,
        mock_api_ids,
        mock_request,
        mock_extracted_ids,
        mock_write,
        mock_print,
        mock_sleep,
    ):
        """
        Test that server error messages are printed for 500-599 status codes.
        At time of writing, test also inadvertantly demonstrates retry loop is working
        """
        #  todo: split testing retry and server error

        # simulate db query returning api_ids
        mock_api_ids.return_value.order_by.return_value.values_list.return_value = [
            "1",
            "2",
        ]
        db_api_ids = (
            mock_api_ids.return_value.order_by.return_value.values_list.return_value
        )

        # simulate extract_api_ids_from_file function, which is called by call_api_and_save_data function
        mock_extracted_ids.return_value = set(["1"])
        extracted_ids = mock_extracted_ids.return_value

        # simulate request and response
        mock_request.return_value.status_code = 500
        responses = [MagicMock() for i in db_api_ids if str(i) not in extracted_ids]
        mock_request.side_effects = lambda: responses

        returned = mock_request.side_effects
        print("returned", returned)

        result = call_api_and_save_data()  # noqa: F841

        mock_print.assert_any_call("Server error (500) for api_id: 2")

    @patch("builtins.open", new_callable=mock_open)
    @patch("members_interest_app.utils.call_registered_interests.time.sleep")
    @patch(
        "members_interest_app.utils.call_registered_interests.extract_api_ids_from_file"
    )
    def test_file_path_passed_to_extract_ids_func(
        self, mock_extract_ids, mock_sleep, mock_open
    ):
        # file_path = MagicMock()
        # file_path_str = file_path.retrun_value="some/file/path"

        file_path_str = "some/file/path"

        call_api_and_save_data(file_path_str)

        mock_extract_ids.assert_called_with(file_path_str)

    # todo: add more testing for other response codes and handling errors
