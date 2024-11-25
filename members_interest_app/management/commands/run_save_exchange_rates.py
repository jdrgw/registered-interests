import traceback

from django.core.management.base import BaseCommand

# from members_interest_app.models import ExchangeRate
from members_interest_app.utils.save_exchange_rates import save_exchange_rates


class Command(BaseCommand):
    help = "saves daily spot rate for GBP to AUD, USD and EUR from static csvs containing Bank of England FX data"

    def handle(self, *args, **options):
        try:
            result = save_exchange_rates()

            self.stdout.write(self.style.SUCCESS(f"Successfully ran: {result}"))
        except Exception as e:
            # Log the full stack trace for unexpected errors
            self.stderr.write(self.style.ERROR("An unexpected error occurred:"))
            self.stderr.write(traceback.format_exc())
