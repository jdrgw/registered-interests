from django.test import TestCase

from members_interest_app.forms import SearchForm


class SearchFormTest(TestCase):
    def test_valid_form(self):
        form_data = {"q": "Test search"}
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form_data = {"q": ""}
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn("q", form.errors)

    def test_form_field_max_length(self):
        form_data = {"q": "a" * 101}  # Exceeding max_length
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("q", form.errors)
