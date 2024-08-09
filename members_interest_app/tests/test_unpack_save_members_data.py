import os
import json
from django.test import TestCase
from unittest import mock
from members_interest_app.utils.unpack_save_members_data import unpack_save_members_data
from members_interest_app.models import MemberOfParliament
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

class TestUnpackSaveMembersDataFunction(TestCase):

    @mock.patch('django.conf.settings.BASE_DIR', new='/mocked/base/dir')
    @mock.patch('builtins.open', new_callable=mock.mock_open, 
                read_data='''[
                    {
                        "value": {
                            "id": 1,
                            "nameDisplayAs": "John Doe",
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
                ]''')
    def test_unpack_save_members_data(self, mock_open):
        """
        Test that the unpack_save_members_data function works as expected
        """
        # Pass a test file name
        result = unpack_save_members_data(file_name='mocked_file.json')

        # Check that the open function was called with the correct arguments
        mock_open.assert_called_once_with(os.path.join(settings.BASE_DIR, "data/members_data/raw_data", 'mocked_file.json'), 'r')

        # Check that the MemberOfParliament objects were created/updated correctly
        member = MemberOfParliament.objects.get(api_id=1)
        self.assertEqual(member.name, 'John Doe')
        self.assertEqual(member.gender, 'Male')
        self.assertEqual(member.thumbnail_url, 'http://example.com')
        self.assertEqual(member.constituency, 'London')
        self.assertEqual(member.membership_start.strftime('%Y-%m-%dT%H:%M:%S'), '2024-01-01T00:00:00')
        self.assertEqual(member.membership_end.strftime('%Y-%m-%dT%H:%M:%S'), '2024-12-31T00:00:00')
        self.assertEqual(member.membership_end_reason, 'Retired')
        self.assertEqual(member.membership_end_notes, 'Retired due to age')
        self.assertEqual(member.house, 'House of Commons')

        # Expected output string
        expected_output = "Total members added: 1, Total members updated: 0, Total errors: 0"
        
        # Assert the output is as expected
        self.assertEqual(result, expected_output)

    @mock.patch('django.conf.settings.BASE_DIR', new='/mocked/base/dir')
    def test_unpack_save_members_data_file_not_found(self):
        """
        Test that the unpack_save_members_data function handles file not found error
        """
        with self.assertRaises(FileNotFoundError):
            # Call the function with a non-existent file
            unpack_save_members_data(file_name='non_existent_file.json')

    @mock.patch('django.conf.settings.BASE_DIR', new='/mocked/base/dir')
    def test_unpack_save_members_data_json_decode_error(self):
        """
        Test that the unpack_save_members_data function handles JSON decoding error
        """
        with mock.patch('builtins.open', new_callable=mock.mock_open, 
                        read_data='Invalid JSON'):
            with self.assertRaises(json.JSONDecodeError):
                # Call the function with the mocked invalid JSON data
                unpack_save_members_data(file_name='mocked_file.json')

    @mock.patch('django.conf.settings.BASE_DIR', new='/mocked/base/dir')
    def test_unpack_save_members_data_null_api_id(self):
        """
        Test that the unpack_save_members_data function handles null or None api_id
        """
        with mock.patch('builtins.open', new_callable=mock.mock_open, 
                        read_data='''[
                            {
                                "value": {
                                    "id": null,
                                    "nameDisplayAs": "John Doe",
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
                        ]'''):
            
            # Call the function with the mocked data where id is null
            unpack_save_members_data(file_name='mocked_file.json')

            # Ensure no MemberOfParliament object is created with null api_id
            with self.assertRaises(ObjectDoesNotExist):
                MemberOfParliament.objects.get(name='John Doe')

    @mock.patch('builtins.open', new_callable=mock.mock_open, 
                read_data='''[
                    {
                        "value": {
                            "id": 1,
                            "nameDisplayAs": "John Doe",
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
                ]''')
    @mock.patch('django.conf.settings.BASE_DIR', new='/mocked/base/dir')
    def test_unpack_save_members_data_output_string(self, mock_open):
        """
        Test that the unpack_save_members_data function returns the correct output string
        """
        # Run the utility function
        result = unpack_save_members_data(file_name='mocked_file.json')

        # Expected output string
        expected_output = "Total members added: 1, Total members updated: 0, Total errors: 0"
        
        # Assert the output is as expected
        self.assertEqual(result, expected_output)
