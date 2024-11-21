import json
from unittest import mock
from unittest.mock import mock_open, patch

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.test import TestCase

from members_interest_app.models import House, MemberOfParliament
from members_interest_app.utils.unpack_save_members_data import unpack_save_members_data


class TestUnpackSaveMembersDataFunction(TestCase):
    print("Using database: ", connection.settings_dict["NAME"])

    fake_data = [
        {
            "value": {
                "id": 1,
                "nameDisplayAs": "Michael Scott",
                "gender": "Male",
                "thumbnailUrl": "http://example.com",
                "latestHouseMembership": {
                    "membershipFrom": "London",
                    "membershipStartDate": "2024-01-01T00:00:00",
                    "membershipEndDate": "2024-12-31T00:00:00",
                    "membershipEndReason": "Retired",
                    "membershipEndReasonNotes": "Retired due to age",
                    "house": 1,
                },
            }
        }
    ]

    fake_data_json = json.dumps(fake_data)

    def setUp(self):
        House.objects.get_or_create(id=1, defaults={"name": "Unknown"})
        House.objects.get_or_create(id=2, defaults={"name": "House of Commons"})
        House.objects.get_or_create(id=3, defaults={"name": "House of Lords"})

    @patch("builtins.open", new_callable=mock_open, read_data=fake_data_json)
    @patch("os.path.join", return_value="fake_path.json")
    def test_file_opened(self, mock_join, mock_open):
        fake_file_path = "fake_path.json"
        result = unpack_save_members_data(fake_file_path)  # noqa F841
        mock_open.assert_called_once_with(fake_file_path, "r")

    @patch("builtins.open", new_callable=mock_open, read_data=fake_data_json)
    @patch("os.path.join", return_value="fake_path.json")
    def test_file_processed(self, mock_join, mock_open):
        fake_file_path = "fake_path.json"
        result = unpack_save_members_data(fake_file_path)  # noqa F841

        member = MemberOfParliament.objects.get(api_id=1)
        house_of_commons = House.objects.get(name="House of Commons")

        self.assertEqual(member.name, "Michael Scott")
        self.assertEqual(member.gender, "Male")
        self.assertEqual(member.thumbnail_url, "http://example.com")
        self.assertEqual(member.constituency, "London")
        self.assertEqual(
            member.membership_start.strftime("%Y-%m-%dT%H:%M:%S"), "2024-01-01T00:00:00"
        )
        self.assertEqual(
            member.membership_end.strftime("%Y-%m-%dT%H:%M:%S"), "2024-12-31T00:00:00"
        )
        self.assertEqual(member.membership_end_reason, "Retired")
        self.assertEqual(member.membership_end_notes, "Retired due to age")
        self.assertEqual(member.house, house_of_commons)

        print(
            "Using database in  file processed at end: ",
            connection.settings_dict["NAME"],
        )

    @patch("builtins.open", new_callable=mock_open, read_data=fake_data_json)
    @patch("os.path.join", return_value="fake_path.json")
    def test_output_string(self, mock_join, mock_open):
        fake_file_path = "fake_path.json"
        result = unpack_save_members_data(fake_file_path)
        # Expected output string
        expected_output = (
            "Total members added: 1, Total members updated: 0, Total errors: 0"
        )

        # Assert the output is as expected
        self.assertEqual(result, expected_output)

    @mock.patch("django.conf.settings.BASE_DIR", new="/mocked/base/dir")
    def test_unpack_save_members_data_null_api_id(self):
        """
        Test that the unpack_save_members_data function handles null or None api_id
        """
        with mock.patch(
            "builtins.open",
            new_callable=mock.mock_open,
            read_data="""[
                            {
                                "value": {
                                    "id": null,
                                    "nameDisplayAs": "Jim Lahey",
                                    "gender": "Male",
                                    "thumbnailUrl": "http://example.com",
                                    "latestHouseMembership": {
                                        "membershipFrom": "London",
                                        "membershipStartDate": "2024-01-01T00:00:00",
                                        "membershipEndDate": "2024-12-31T00:00:00",
                                        "membershipEndReason": "Retired",
                                        "membershipEndReasonNotes": "Retired due to age",
                                        "house": 1
                                    }
                                }
                            }
                        ]""",
        ):
            # Call the function with the mocked data where id is null
            unpack_save_members_data(file_name="mocked_file.json")

            # Ensure no MemberOfParliament object is created with null api_id
            with self.assertRaises(ObjectDoesNotExist):
                MemberOfParliament.objects.get(name="Jim Lahey")
