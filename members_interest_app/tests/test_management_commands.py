from django.test import TestCase
from io import StringIO
from django.core.management import call_command

class TestRunUnpackSaveMembersData(TestCase):
    def test_management_command_output(self):
        out = StringIO()
        call_command("run_unpack_save_members_data", stdout=out)
        result = out.getvalue()
        expected_output_slice = "Total members added:"
        self.assertIn(expected_output_slice, result)
