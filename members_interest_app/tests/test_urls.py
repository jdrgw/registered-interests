from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse

from members_interest_app.views import (
    index,
    members_of_parliament,
    registered_interest_profile,
    registered_interests,
)


class TestUrls(SimpleTestCase):
    def test_index_page_page_url_is_resolved(self):
        url = reverse("index-page")

        self.assertEquals(resolve(url).func, index)

    def test_members_of_parliament_url_is_resolved(self):
        url = reverse("members-of-parliament")

        self.assertEquals(resolve(url).func, members_of_parliament)

    def test_registered_interests_url_is_resolved(self):
        url = reverse("registered-interests")

        self.assertEquals(resolve(url).func, registered_interests)

    def test_registered_interests_profile_url_is_resolved(self):
        pk = 1  # Example primary key for the test
        url = reverse("registered-interest-profile", args=[pk])

        self.assertEquals(resolve(url).func, registered_interest_profile)
