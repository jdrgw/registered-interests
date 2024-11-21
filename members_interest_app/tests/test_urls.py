from django.test import SimpleTestCase
from django.urls import resolve, reverse

from members_interest_app.views import (
    index,
    members_of_parliament,
)


class TestUrls(SimpleTestCase):
    def test_index_page_page_url_is_resolved(self):
        url = reverse("index-page")

        self.assertEquals(resolve(url).func, index)

    def test_members_of_parliament_url_is_resolved(self):
        url = reverse("members-of-parliament")

        self.assertEquals(resolve(url).func, members_of_parliament)
