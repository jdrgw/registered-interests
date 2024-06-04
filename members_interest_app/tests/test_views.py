from django.test import TestCase, Client
from django.urls import reverse

class TestViews(TestCase):
    def test_index_view(self):
        client = Client()
        response = client.get(reverse("index-page"))

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "members_interest_app/index.html")

    def test_members_of_parliament_view(self):
        client = Client()
        response = client.get(reverse("members-of-parliament"))

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "members_interest_app/members-of-parliament.html")
