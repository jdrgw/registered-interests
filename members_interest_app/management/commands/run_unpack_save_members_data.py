from django.core.management.base import BaseCommand, CommandError
from members_interest_app.utils import unpack_save_members_data

class Command(BaseCommand):
    help = "run the custom util function unpack_save_members_data to download and save MPs to the database"

    def handle(self, *args, **kwargs):
        try:
            run = unpack_save_members_data()
            return run
        except Exception as e:
            print(f"The following exception occurred: {e}. Read the logs for more detail")
