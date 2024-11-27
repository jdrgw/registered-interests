from django.core.management.base import BaseCommand

from members_interest_app.utils.convert_interest_amount_to_gbp import (
    convert_interest_amount_to_gbp,
)


class Command(BaseCommand):
    help = "Converts all RegisteredInterest interest amounts to GBP and updates the gbp_interest_amount field."

    def handle(self, *args, **kwargs):
        try:
            message = convert_interest_amount_to_gbp()
            self.stdout.write(self.style.SUCCESS(message))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {str(e)}"))
