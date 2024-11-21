# members_interest_app/management/commands/process_registered_interests.py

from django.core.management.base import BaseCommand
from members_interest_app.utils.unpack_registered_interests import (
    extract_preprocess_interest_data,
    extract_currencies_and_amounts,
    extract_third_party_details,
    clean_and_save_to_database,
)


class Command(BaseCommand):
    help = "Processes registered interest data and saves to the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Path to the JSON file containing registered interest data",
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs["file_path"]

        try:
            data = extract_preprocess_interest_data(file_path)
            amts = extract_currencies_and_amounts(data)
            third_party = extract_third_party_details(amts)
            records_created = clean_and_save_to_database(third_party)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Data processing completed successfully! {records_created} records were inserted."
                )
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {str(e)}"))
