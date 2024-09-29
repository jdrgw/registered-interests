from django_test_migrations.contrib.unittest_case import MigratorTestCase
from django.db import connection


class TestMigration0004(MigratorTestCase):

    migrate_from = ('members_interest_app', '0003_memberofparliament_house_fk')
    migrate_to = ('members_interest_app', '0004_memberofparliament_house_fk_data_migration')

    def prepare(self):
        """Prepare some data before the migration."""
        MemberOfParliament = self.old_state.apps.get_model("members_interest_app", "MemberOfParliament")
        # Create some initial test data
        MemberOfParliament.objects.create(name="John Doe", house="House of Commons", api_id=1)
        MemberOfParliament.objects.create(name="Jane Doe", house="House of Lords", api_id=2)
        MemberOfParliament.objects.create(name="Alex Smith", house="Unknown", api_id=3)
        MemberOfParliament.objects.create(name="Chris Johnson", house="Other", api_id=4)

    def test_migration_forwards(self):
        """Test the data after the migration has been applied."""
        House = self.new_state.apps.get_model("members_interest_app", "House")
        MemberOfParliament = self.new_state.apps.get_model("members_interest_app", "MemberOfParliament")

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
        assert chris_johnson.house_fk.name == "Unknown"  # Should be set to Unknown by default

        print("Using database: ", connection.settings_dict['NAME'])


    # def test_migration_backwards(self):
    #     """Test the data after the migration has been reversed."""
    #     MemberOfParliament = self.old_state.apps.get_model("members_interest_app", "MemberOfParliament")
    #     House = self.old_state.apps.get_model("members_interest_app", "House")

    #     # Check that the `house_fk` field is null and the `house` field was restored
    #     john_doe = MemberOfParliament.objects.get(name="John Doe")
    #     assert john_doe.house_fk is None
    #     assert john_doe.house == "House of Commons"

    #     jane_doe = MemberOfParliament.objects.get(name="Jane Doe")
    #     assert jane_doe.house_fk is None
    #     assert jane_doe.house == "House of Lords"

    #     alex_smith = MemberOfParliament.objects.get(name="Alex Smith")
    #     assert alex_smith.house_fk is None
    #     assert alex_smith.house == "Unknown"

    #     chris_johnson = MemberOfParliament.objects.get(name="Chris Johnson")
    #     assert chris_johnson.house_fk is None
    #     assert chris_johnson.house == "Other"

    #     # Check that the `House` entries were deleted
    #     assert not House.objects.filter(name="House of Commons").exists()
    #     assert not House.objects.filter(name="House of Lords").exists()
    #     assert not House.objects.filter(name="Unknown").exists()
















# from django.test import TestCase
# from django.apps import apps
# from django_test_migrations.contrib.unittest_case import MigratorTestCase

# class TestMigration0004(MigratorTestCase):

#     migrate_from = ('members_interest_app', '0003_memberofparliament_house_fk')
#     migrate_to = ('members_interest_app', '0004_memberofparliament_house_fk_data_migration')

#     def setUpBeforeMigration(self, apps):
#         """
#         This method runs before the migration is applied.
#         You can set up any initial data here that should be migrated.
#         """
#         MemberOfParliament = apps.get_model("members_interest_app", "MemberOfParliament")
#         # Create some initial test data
#         MemberOfParliament.objects.create(name="John Doe", house="House of Commons")
#         MemberOfParliament.objects.create(name="Jane Doe", house="House of Lords")
#         MemberOfParliament.objects.create(name="Alex Smith", house="Unknown")
#         MemberOfParliament.objects.create(name="Chris Johnson", house="Other")

#     def test_migration_forwards(self):
#         """
#         This method runs after the migration is applied.
#         Check if the migration did what it was supposed to do.
#         """
#         House = self.apps.get_model("members_interest_app", "House")
#         MemberOfParliament = self.apps.get_model("members_interest_app", "MemberOfParliament")

#         # Check that the `House` entries were created
#         self.assertTrue(House.objects.filter(name="House of Commons").exists())
#         self.assertTrue(House.objects.filter(name="House of Lords").exists())
#         self.assertTrue(House.objects.filter(name="Unknown").exists())

#         # Check that the `house_fk` field was updated correctly
#         john_doe = MemberOfParliament.objects.get(name="John Doe")
#         self.assertEqual(john_doe.house_fk.name, "House of Commons")

#         jane_doe = MemberOfParliament.objects.get(name="Jane Doe")
#         self.assertEqual(jane_doe.house_fk.name, "House of Lords")

#         alex_smith = MemberOfParliament.objects.get(name="Alex Smith")
#         self.assertEqual(alex_smith.house_fk.name, "Unknown")

#         chris_johnson = MemberOfParliament.objects.get(name="Chris Johnson")
#         self.assertEqual(chris_johnson.house_fk.name, "Unknown")  # Should be set to Unknown by default

#     def test_migration_backwards(self):
#         """
#         This method runs after the migration is reversed.
#         Check if the reverse migration undoes the changes correctly.
#         """
#         MemberOfParliament = self.apps.get_model("members_interest_app", "MemberOfParliament")
#         House = self.apps.get_model("members_interest_app", "House")

#         # Check that the `house_fk` field is null and the `house` field was restored
#         john_doe = MemberOfParliament.objects.get(name="John Doe")
#         self.assertIsNone(john_doe.house_fk)
#         self.assertEqual(john_doe.house, "House of Commons")

#         jane_doe = MemberOfParliament.objects.get(name="Jane Doe")
#         self.assertIsNone(jane_doe.house_fk)
#         self.assertEqual(jane_doe.house, "House of Lords")

#         alex_smith = MemberOfParliament.objects.get(name="Alex Smith")
#         self.assertIsNone(alex_smith.house_fk)
#         self.assertEqual(alex_smith.house, "Unknown")

#         chris_johnson = MemberOfParliament.objects.get(name="Chris Johnson")
#         self.assertIsNone(chris_johnson.house_fk)
#         self.assertEqual(chris_johnson.house, "Other")

#         # Check that the `House` entries were deleted
#         self.assertFalse(House.objects.filter(name="House of Commons").exists())
#         self.assertFalse(House.objects.filter(name="House of Lords").exists())
#         self.assertFalse(House.objects.filter(name="Unknown").exists())
