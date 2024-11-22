import math

from django.test import Client, TestCase
from django.urls import reverse

from members_interest_app.models import (
    House,
    MemberOfParliament,
    RegisteredInterest,
)


class TestViews(TestCase):
    def test_index_view(self):
        client = Client()
        response = client.get(reverse("index-page"))

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "members_interest_app/index.html")


class MembersOfParliamentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.range = 40
        for i in range(1, self.range):
            MemberOfParliament.objects.create(name=f"member {i}", api_id=f"{i}")
        self.response = self.client.get(reverse("members-of-parliament"))

    def test_members_of_parliament_view_response(self):
        self.assertEquals(self.response.status_code, 200)
        self.assertTemplateUsed(
            self.response, "members_interest_app/members-of-parliament.html"
        )

    def test_num_members_and_pages(self):
        members = self.response.context["members"]
        total_members_count = members.paginator.count
        members_per_page = members.paginator.per_page

        total_pages = total_members_count // members_per_page
        if total_members_count % members_per_page != 0:
            total_pages += 1

        self.assertEquals(total_members_count, self.range - 1)
        self.assertEqual(total_pages, members.paginator.num_pages)


class TestMemberProfileView(TestCase):
    def setUp(self):
        House.objects.all().delete()  # 0004 migration file creates house objects
        House.objects.create(name="House of Commons")

        # Create a test member of parliament
        self.member = MemberOfParliament.objects.create(
            name="Ron Swanson",
            api_id="123",
            gender="Male",
            thumbnail_url="http://example.com/image.jpg",
            constituency="Example Constituency",
            membership_start="2020-01-01",
            membership_end="2024-01-01",
            membership_end_reason="Resigned",
            membership_end_notes="Dislikes government, extreme libertarian",
            house=House.objects.get(name="House of Commons"),
        )

    def test_existing_member(self):
        client = Client()
        response = client.get(reverse("member", args=[self.member.pk]))

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, "members_interest_app/member.html")
        self.assertContains(response, self.member.name)

    def test_non_existent_member(self):
        client = Client()
        response = client.get(reverse("member", args=[0]))
        self.assertEquals(response.status_code, 404)


class TestRegisteredInterestView(TestCase):
    def setUp(self):
        self.client = Client()
        self.range = 60
        self.member = MemberOfParliament.objects.create(name="Michael Scott", api_id=1)

        for i in range(1, self.range):
            RegisteredInterest.objects.create(
                member_of_parliament=self.member,
                api_id=f"api_id_{i}",
                unique_api_generated_id=f"unique_id_{i}",
                category_id=f"cat_id_{i}",
                category_name=f"Category {i}",
                sort_order=str(i),
                date_created="2024-01-01",
                interest_summary=f"Summary for interest {i}"  # Optional, but adding for realism
            )
        self.response = self.client.get(reverse("registered-interests"))

    def test_registered_interests_view_response(self):
        self.assertEquals(self.response.status_code, 200)
        self.assertTemplateUsed(
            self.response, "members_interest_app/registered-interests.html"
        )

    def test_num_members_and_pages(self):
        registered_interests = self.response.context["registered_interests"]
        registered_interests_count = registered_interests.paginator.count
        registered_interests_per_page = registered_interests.paginator.per_page

        total_pages = math.ceil(registered_interests_count / registered_interests_per_page)

        self.assertEquals(registered_interests_count, self.range - 1)
        self.assertEqual(total_pages, registered_interests.paginator.num_pages)
