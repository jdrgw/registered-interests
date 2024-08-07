from django.test import TestCase
from io import StringIO
from django.core.management import call_command
from unittest.mock import patch

class TestRunUnpackSaveMembersData(TestCase):
    def test_management_command_output(self):
        out = StringIO()
        call_command("run_unpack_save_members_data", stdout=out)
        result = out.getvalue()
        expected_output_slice = "Total members added:"
        self.assertIn(expected_output_slice, result)

class TestCallMembersAPI(TestCase):

    @patch('members_interest_app.utils.call_members_api.fetch_members_data')
    def test_management_command_output(self, mock_fetch_members_data):
        # Setup the mock return value
        mock_fetch_members_data.return_value = "Mocked fetch_members_data function called"
        out = StringIO()
        call_command("call_members_api", stdout=out)
        self.assertIn("Mocked fetch_members_data function called", out.getvalue())

        mock_fetch_members_data.assert_called_once()
