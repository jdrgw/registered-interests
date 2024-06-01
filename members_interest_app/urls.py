from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index-page'),
    path('members-of-parliament/', views.members_of_parliament, name='members-of-parliament'),
]