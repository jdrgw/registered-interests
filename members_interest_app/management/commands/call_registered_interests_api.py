from django.core.management.base import BaseCommand, CommandError
from members_interest_app.utils.call_registered_interests import call_api_and_save_data


class Command(BaseCommand):
    help = "Run the custom util function to download and save registered interest data for MPs to a JSON file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file_name",
            type=str,
            help="Optional: The JSON file where the registered interest data will be extracted from and/or saved. If not provided, a default file will be used."
        )

    def handle(self, *args, **kwargs):
        file_name = kwargs.get("file_name")

        try:
            if file_name:
                result = call_api_and_save_data(file_name)
            else:
                result = call_api_and_save_data()

            self.stdout.write(self.style.SUCCESS(result))
        except Exception as e:
            raise CommandError(
                f"The following exception occurred: {e}. Read the logs for more details."
            )
