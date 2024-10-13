from django_test_migrations.contrib.unittest_case import MigratorTestCase
from django.db import connection


class TestMigration0004(MigratorTestCase):
    migrate_from = ("members_interest_app", "0003_memberofparliament_house_fk")
    migrate_to = (
        "members_interest_app",
        "0004_memberofparliament_house_fk_data_migration",
    )

    def prepare(self):
        """Prepare some data before the migration."""
        MemberOfParliament = self.old_state.apps.get_model(
            "members_interest_app", "MemberOfParliament"
        )
        # Create some initial test data
        MemberOfParliament.objects.create(
            name="John Doe", house="House of Commons", api_id=1
        )
        MemberOfParliament.objects.create(
            name="Jane Doe", house="House of Lords", api_id=2
        )
        MemberOfParliament.objects.create(name="Alex Smith", house="Unknown", api_id=3)
        MemberOfParliament.objects.create(name="Chris Johnson", house="Other", api_id=4)

    def test_migration_forwards(self):
        """Test the data after the migration has been applied."""
        House = self.new_state.apps.get_model("members_interest_app", "House")
        MemberOfParliament = self.new_state.apps.get_model(
            "members_interest_app", "MemberOfParliament"
        )

        # Check that the `House` entries were created
        assert House.objects.filter(name="House of Commons").exists()
        assert House.objects.filter(name="House of Lords").exists()
        assert House.objects.filter(name="Unknown").exists()

        # Check that the `house_fk` field was updated correctly
        john_doe = MemberOfParliament.objects.get(name="John Doe")
        assert john_doe.house_fk.name == "House of Commons"

        jane_doe = MemberOfParliament.objects.get(name="Jane Doe")
        assert jane_doe.house_fk.name == "House of Lords"

        alex_smith = MemberOfParliament.objects.get(name="Alex Smith")
        assert alex_smith.house_fk.name == "Unknown"

        chris_johnson = MemberOfParliament.objects.get(name="Chris Johnson")
        assert (
            chris_johnson.house_fk.name == "Unknown"
        )  # Should be set to Unknown by default

        print("Using database: ", connection.settings_dict["NAME"])
