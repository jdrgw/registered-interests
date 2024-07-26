from django.core.management.base import BaseCommand, CommandError
from members_interest_app.utils.utils import unpack_save_members_data

class Command(BaseCommand):
    help = "run the custom util function unpack_save_members_data to download and save MPs to the database"

    def handle(self, *args, **kwargs):
        try:
            result = unpack_save_members_data()
            self.stdout.write(result)
        except Exception as e:
            self.stdout.write(f"The following exception occurred: {e}. Read the logs for more detail")
