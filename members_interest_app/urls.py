from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index-page"),
    path(
        "members-of-parliament/",
        views.members_of_parliament,
        name="members-of-parliament",
    ),
    path("member/<int:pk>/", views.member, name="member"),
    path(
        "registered-interests/", views.registered_interests, name="registered-interests"
    ),
    path(
        "registered-interest-profile/<int:pk>/",
        views.registered_interest_profile,
        name="registered-interest-profile",
    ),
    path("stats/", views.stats, name="stats"),
]
