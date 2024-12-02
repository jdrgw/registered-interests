from django.test import SimpleTestCase
from django.urls import resolve, reverse

from members_interest_app.views import (
    index,
    member_profile,
    members_of_parliament,
    registered_interest_profile,
    registered_interests,
    search_results,
    stats,
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

    def test_member_profile_url_is_resolved(self):
        pk = 1  # Example primary key for the test
        url = reverse("member", args=[pk])

        self.assertEquals(resolve(url).func, member_profile)

    def test_stats_url_is_resolved(self):
        url = reverse("stats")

        self.assertEquals(resolve(url).func, stats)

    def test_search_results_url_is_resolved(self):
        url = reverse("search-results")

        self.assertEquals(resolve(url).func, search_results)
