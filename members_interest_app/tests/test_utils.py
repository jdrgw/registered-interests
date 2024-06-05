import os
import json
from django.test import TestCase
from unittest import mock
from members_interest_app.utils import unpack_save_members_data
from members_interest_app.models import MemberOfParliament
from django.core.exceptions import ObjectDoesNotExist


class TestUnpackSaveMembersDataFunction(TestCase):
    @mock.patch('members_interest_app.utils.os.path.dirname', return_value='/mocked/directory')
    @mock.patch('members_interest_app.utils.os.path.abspath', side_effect=lambda path: path.replace('/mocked/absolute/test/path', '/Users/jamie/repos/parliament_repo/parliament_data/members_interest_app/'))
    @mock.patch('members_interest_app.utils.open', new_callable=mock.mock_open, 
                read_data='''[
                    {
                        "value": {
                            "id": 1,
                            "nameDisplayAs": "John Doe",
                            "gender": "Male",
                            "thumbnailUrl": "http://example.com",
                            "latestHouseMembership": {
                                "membershipFrom": "London",
                                "membershipStartDate": "2024-01-01",
                                "membershipEndDate": "2024-12-31",
                                "membershipEndReason": "Retired",
                                "membershipEndReasonNotes": "Retired due to age",
                                "house": 1
                            }
                        }
                    }
                ]''')
    def test_unpack_save_members_data(self, mock_open, mock_abspath, mock_dirname):
        """
        Test that the unpack_save_members_data function works as expected
        """
        current_dir = os.path.abspath(os.path.dirname(__file__))
        members_json_file = os.path.abspath(os.path.join(current_dir, '../../call_members_api/members_of_parliament.json'))
        
        run = unpack_save_members_data()

        # Check that the open function was called with the correct arguments
        mock_open.assert_called_once_with(members_json_file, 'r')

        # Check that the MemberOfParliament objects were created/updated correctly
        member = MemberOfParliament.objects.get(api_id=1)
        self.assertEqual(member.name, 'John Doe')
        self.assertEqual(member.gender, 'Male')
        self.assertEqual(member.thumbnail_url, 'http://example.com')
        self.assertEqual(member.constituency, 'London')
        self.assertEqual(member.membership_start.strftime('%Y-%m-%d'), '2024-01-01')
        self.assertEqual(member.membership_end.strftime('%Y-%m-%d'), '2024-12-31')
        self.assertEqual(member.membership_end_reason, 'Retired')
        self.assertEqual(member.membership_end_notes, 'Retired due to age')
        self.assertEqual(member.house, 'House of Commons')
        print(run)

    @mock.patch('members_interest_app.utils.os.path.dirname', return_value='/mocked/directory')
    @mock.patch('members_interest_app.utils.os.path.abspath', side_effect=lambda path: path.replace('/mocked/absolute/test/path', '/Users/jamie/repos/parliament_repo/parliament_data/members_interest_app/'))
    def test_unpack_save_members_data_file_not_found(self, mock_abspath, mock_dirname):
        """
        Test that the unpack_save_members_data function handles file not found error
        """
        with self.assertRaises(FileNotFoundError):
            # Call the function
            unpack_save_members_data()


    @mock.patch('members_interest_app.utils.os.path.dirname', return_value='/mocked/directory')
    @mock.patch('members_interest_app.utils.os.path.abspath', side_effect=lambda path: path.replace('/mocked/absolute/test/path', '/Users/jamie/repos/parliament_repo/parliament_data/members_interest_app/'))
    def test_unpack_save_members_data_json_decode_error(self, mock_abspath, mock_dirname):
        """
        Test that the unpack_save_members_data function handles JSON decoding error
        """
        with mock.patch('members_interest_app.utils.open', new_callable=mock.mock_open, 
                        read_data='Invalid JSON'):
            with self.assertRaises(json.JSONDecodeError):
                # Call the function
                unpack_save_members_data()

    @mock.patch('members_interest_app.utils.os.path.dirname', return_value='/mocked/directory')
    @mock.patch('members_interest_app.utils.os.path.abspath', side_effect=lambda path: path.replace('/mocked/absolute/test/path', '/Users/jamie/repos/parliament_repo/parliament_data/members_interest_app/'))
    def test_unpack_save_members_data_null_api_id(self, mock_abspath, mock_dirname):
        """
        Test that the unpack_save_members_data function handles null or None api_id
        """
        with mock.patch('members_interest_app.utils.open', new_callable=mock.mock_open, 
                        read_data='''[
                            {
                                "value": {
                                    "id": null,
                                    "nameDisplayAs": "John Doe",
                                    "gender": "Male",
                                    "thumbnailUrl": "http://example.com",
                                    "latestHouseMembership": {
                                        "membershipFrom": "London",
                                        "membershipStartDate": "2024-01-01",
                                        "membershipEndDate": "2024-12-31",
                                        "membershipEndReason": "Retired",
                                        "membershipEndReasonNotes": "Retired due to age",
                                        "house": 1
                                    }
                                }
                            }
                        ]'''):
            
            # Call the function
            unpack_save_members_data()

            # Ensure no MemberOfParliament object is created with null api_id
            with self.assertRaises(ObjectDoesNotExist):
                MemberOfParliament.objects.get(name='John Doe')