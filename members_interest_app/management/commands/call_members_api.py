from django.core.management.base import BaseCommand, CommandError

from members_interest_app.utils.call_members_api import fetch_members_data


class Command(BaseCommand):
    help = "run the custom util function fetch_members_data to download and save MPs data to JSON file"

    def handle(self, *args, **kwargs):
        try:
            result = fetch_members_data()
            self.stdout.write(result)
        except Exception as e:
            raise CommandError(
                f"The following exception occurred: {e}. Read the logs for more detail"
            )
