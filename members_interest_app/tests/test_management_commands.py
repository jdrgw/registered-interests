from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase


class TestRunUnpackSaveMembersDataCommand(TestCase):
    @patch(
        "members_interest_app.utils.unpack_save_members_data.unpack_save_members_data"
    )
    def test_management_command_output(self, mock_unpack_save_members_data):
        """
        Test that the management command calls the unpack_save_members_data function correctly
        and handles its output.
        """
        # Mock return value of the utility function to simulate what it would return
        mock_unpack_save_members_data.return_value = (
            "Total members added: 1, Total members updated: 0, Total errors: 0"
        )

        # Capture the command's output
        out = StringIO()
        file_name = "mocked_file.json"
        call_command("run_unpack_save_members_data", file_name, stdout=out)

        # Verify the utility function was called with the correct argument
        mock_unpack_save_members_data.assert_called_once_with(file_name)

        # Check that the command output includes the utility function's return value
        self.assertIn("Total members added: 1", out.getvalue())
        self.assertIn("Total members updated: 0", out.getvalue())
        self.assertIn("Total errors: 0", out.getvalue())


class TestCallMembersAPI(TestCase):
    @patch("members_interest_app.utils.call_members_api.fetch_members_data")
    def test_management_command_output(self, mock_fetch_members_data):
        # Setup the mock return value
        mock_fetch_members_data.return_value = (
            "Mocked fetch_members_data function called"
        )
        out = StringIO()
        call_command("call_members_api", stdout=out)
        self.assertIn("Mocked fetch_members_data function called", out.getvalue())

        mock_fetch_members_data.assert_called_once()


class TestUnpackAndSaveRegistredInterest(TestCase):
    "This class is intentionally left blank as the management command is not directly tested."

    pass


class RunDSaveExchangeRates(TestCase):
    "This class is intentionally left blank as the management command is not directly tested."

    pass


class RunConvertInterestAmountToGBP(TestCase):
    "This class is intentionally left blank as the management command is not directly tested."

    pass
