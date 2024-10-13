from django.core.management.base import BaseCommand
from members_interest_app.utils.unpack_save_members_data import unpack_save_members_data


class Command(BaseCommand):
    help = "run the custom util function unpack_save_members_data to download and save MPs to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_name",
            type=str,
            help="The name of the JSON file containing MP data, not the filepath",
        )

    def handle(self, *args, **kwargs):
        file_name = kwargs[
            "file_name"
        ]  # Access the file_name passed from the command line
        try:
            result = unpack_save_members_data(file_name)
            self.stdout.write(result)
        except Exception as e:
            self.stdout.write(
                f"The following exception occurred: {e}. Read the logs for more detail"
            )
