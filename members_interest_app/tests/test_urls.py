from django.test import SimpleTestCase
from django.urls import reverse, resolve
from members_interest_app.views import (
    index,
    members_of_parliament,
)

class TestUrls(SimpleTestCase):

    def test_index_page_page_url_is_resolved(self):
        url = reverse('index-page')

        self.assertEquals(resolve(url).func, index)


    def test_members_of_parliament_url_is_resolved(self):
        url = reverse('members-of-parliament')

        self.assertEquals(resolve(url).func, members_of_parliament)



# urlpatterns = [
#     path('', views.index, name='index-page'),
#     path('members-of-parliament/', views.members_of_parliament, name='members-of-parliament'),
# ]