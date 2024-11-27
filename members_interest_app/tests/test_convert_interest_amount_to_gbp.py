from datetime import datetime

from django.test import TestCase

from members_interest_app.models import (
    ExchangeRate,
    MemberOfParliament,
    RegisteredInterest,
)
from members_interest_app.utils.convert_interest_amount_to_gbp import (
    convert_interest_amount_to_gbp,
)


class ConvertInterestAmountToGBPTests(TestCase):
    def setUp(self):
        # Create test exchange rates
        ExchangeRate.objects.create(date="2024-01-01", currency="USD", rate_to_gbp=0.8)
        ExchangeRate.objects.create(date="2024-01-01", currency="EUR", rate_to_gbp=0.9)
        member = MemberOfParliament.objects.create(api_id=1, name="Captain Holt")

        # Create test registered interests
        RegisteredInterest.objects.create(
            member_of_parliament=member,
            api_id=1,
            unique_api_generated_id=1,
            interest_amount=100,
            interest_currency="USD",
            date_created=datetime(2024, 1, 2),
        )
        RegisteredInterest.objects.create(
            member_of_parliament=member,
            api_id=2,
            unique_api_generated_id=2,
            interest_amount=200,
            interest_currency="EUR",
            date_created=datetime(2024, 1, 2),
        )
        RegisteredInterest.objects.create(
            member_of_parliament=member,
            api_id=3,
            unique_api_generated_id=3,
            interest_amount=300,
            interest_currency="GBP",
            date_created=datetime(2024, 1, 2),
        )

    def test_conversion(self):
        # Run the conversion
        message = convert_interest_amount_to_gbp()

        # Verify conversion
        interests = RegisteredInterest.objects.all()
        self.assertEqual(interests[0].gbp_interest_amount, 80.0)  # USD -> GBP
        self.assertEqual(interests[1].gbp_interest_amount, 180.0)  # EUR -> GBP
        self.assertEqual(interests[2].gbp_interest_amount, 300.0)  # GBP -> GBP

        # Check success message
        self.assertIn("GBP interest amounts updated successfully", message)
