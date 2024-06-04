from django.test import TestCase
from django.core.exceptions import ValidationError
from members_interest_app.models import MemberOfParliament

class TestMemberOfParliament(TestCase):
    
    def setUp(self):
        self.member1 = (
            MemberOfParliament
            .objects
            .create(
                api_id=1234, 
                name="Jim Lahey",
                house="Trailer",
                constituency="Trailer Park"
            )
        )
        self.member2 = (
            MemberOfParliament
            .objects
            .create(
                api_id=12345, 
                name="J-roc",
            )
        )
    
    def test_string_print(self):
        expected_string = "Jim Lahey, Trailer, Trailer Park"
        self.assertEqual(str(self.member1), expected_string)

    # Test cleaning and saving member with duplicate api_id
    def test_clean_method_with_existing_api_id(self):
        member = MemberOfParliament(api_id=1234, name="J-roc")
     
        with self.assertRaises(ValidationError):
            member.clean()
    
    def test_save_method_with_existing_api_id(self):
        self.member2.api_id = 1234
    
        with self.assertRaises(ValidationError):
            self.member2.save()

    # Test cleaning and saving member with new api_id
    def test_clean_method_with_new_api_id(self):
        member = MemberOfParliament(api_id=1, name="Randy")
     
        member.clean()

        self.assertEqual(member.api_id, 1)
        self.assertEqual(member.name, "Randy")

    
    def test_save_method_with_new_api_id(self):
        member = MemberOfParliament(api_id=1, name="Randy")
        member.save()

        # Act
        member.api_id = 4321
        member.save()

        # Assert
        member.refresh_from_db()  # Reload the member from the database to ensure changes were saved
        self.assertEqual(member.api_id, "4321")
        self.assertEqual(member.name, "Randy")










