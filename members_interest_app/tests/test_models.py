from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from members_interest_app.models import (
    ExchangeRate,
    House,
    MemberOfParliament,
    RegisteredInterest,
)


class TestMemberOfParliament(TestCase):
    def setUp(self):
        self.trailer = House.objects.create(name="Trailer")

        self.member1 = MemberOfParliament.objects.create(
            api_id=1234,
            name="Jim Lahey",
            house=self.trailer,
            constituency="Trailer Park",
        )
        self.member2 = MemberOfParliament.objects.create(
            api_id=12345,
            name="J-roc",
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

    def test_house_field_defaults_to_unknown(self):
        unknown_house = House.objects.get(name="Unknown")
        self.assertEqual(self.member2.house, unknown_house)


class TestHouse(TestCase):
    def setUp(self):
        self.commons = House.objects.create(name="commons")

    def test_string_print(self):
        # test whether str returns expected value
        expected_string = "commons"
        self.assertEqual(str(self.commons), expected_string)

    def test_no_name(self):
        "Test that creating a House without a name raises ValidationError"
        with self.assertRaises(ValidationError):
            # Create a House with name=None, which should raise a ValidationError
            house = House(name=None)
            house.full_clean()


class RegisteredInterestModelTests(TestCase):
    def setUp(self):
        self.mp = MemberOfParliament.objects.create(api_id="123", name="Ron Swanson")

    def test_save_registered_interest_with_valid_mp(self):
        registered_interest = RegisteredInterest(
            member_of_parliament=self.mp,
            api_id="interest_001",
            unique_api_generated_id="unique_id_001",
            category_id="category_001",
            category_name="Category Name",
            sort_order="1",
            interest_summary="Summary of interest",
            date_created=timezone.now(),
            date_last_amended=timezone.now(),
            date_deleted=None,
            is_correction=False,
            is_child_interest=False,
            parent_interest="1",
            interest_amount=100.00,
            interest_currency="GBP",
            number_of_extracted_amounts=None,
            contains_loan=False,
            contains_time_period=None,
            payer="John Smith",
            payer_type="person",
            payer_address=None,
            payer_companies_house_id=None,
            purpose="Purpose of the interest",
            role="Role in interest",
            employer_name="Pawnee",
            family_member_name=None,
            family_member_relationship=None,
            family_member_role=None,
            family_member_paid_by_mp_or_parliament=None,
            family_member_lobbies=True,
        )

        try:
            registered_interest.save()
        except ValidationError:
            self.fail("RegisteredInterest.save() raised ValidationError unexpectedly!")

        self.assertEqual(RegisteredInterest.objects.count(), 1)

    def test_save_registered_interest_with_invalid_mp(self):
        registered_interest = RegisteredInterest(
            member_of_parliament=None,  # Invalid member_of_parliament
            api_id="interest_002",
            unique_api_generated_id="unique_id_002",
            category_id="category_002",
            category_name="Category Name 2",
            sort_order="2",
            interest_summary="Summary of interest 2",
            date_created=timezone.now(),
            date_last_amended=timezone.now(),
            date_deleted=None,
            is_correction=False,
            is_child_interest=False,
            parent_interest="1",
            interest_amount=None,
            interest_currency=None,
            number_of_extracted_amounts=None,
            contains_loan=None,
            contains_time_period=None,
            payer=None,
            payer_type=None,
            payer_address=None,
            payer_companies_house_id=None,
            purpose=None,
            role="Role in interest",
            employer_name="Pawnee",
            family_member_name=None,
            family_member_relationship=None,
            family_member_role=None,
            family_member_paid_by_mp_or_parliament=None,
            family_member_lobbies=True,
        )

        with self.assertRaises(IntegrityError):
            registered_interest.save()

    def test_string_representation(self):
        registered_interest = RegisteredInterest(
            member_of_parliament=self.mp,
            api_id="interest_003",
            category_id="category_003",
            category_name="Category Name 3",
            sort_order="3",
            interest_summary="Another summary of interest",
            date_created=timezone.now(),
            date_last_amended=timezone.now(),
        )

        self.assertEqual(
            str(registered_interest), "Category Name 3 - Another summary of interest"
        )


class ExchangeRateModelTest(TestCase):
    def setUp(self):
        # Create an ExchangeRate instance for testing
        self.exchange_rate = ExchangeRate.objects.create(
            date="2023-11-23",
            currency="USD",
            rate_to_gbp=0.7500
        )

    def test_exchange_rate_creation(self):
        # Test if the ExchangeRate instance is created correctly
        self.assertEqual(self.exchange_rate.date, "2023-11-23")
        self.assertEqual(self.exchange_rate.currency, "USD")
        self.assertEqual(self.exchange_rate.rate_to_gbp, 0.7500)
