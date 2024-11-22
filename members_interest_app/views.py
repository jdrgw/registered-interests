from django.core.paginator import Paginator
from django.db.models import Case, Value, When
from django.db.models.functions import Substr
from django.shortcuts import get_object_or_404, render

from .models import MemberOfParliament, RegisteredInterest

# Create your views here.


def index(request):
    return render(request, "members_interest_app/index.html")


def members_of_parliament(request):
    members = MemberOfParliament.objects.all().values(
        "id",
        "name",
        "gender",
        "thumbnail_url",
        "constituency",
        "membership_start",
        "membership_end",
        "membership_end_reason",
        "membership_end_notes",
        "house",
    )

    paginator = Paginator(members, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {"members": page_obj}

    return render(request, "members_interest_app/members-of-parliament.html", context)


def member(request, pk):
    member = get_object_or_404(MemberOfParliament, pk=pk)
    context = {"member": member}
    return render(request, "members_interest_app/member.html", context)


def registered_interests(request):
    registered_interests = (
        RegisteredInterest
        .objects
        .annotate(
            has_financial=Case(
                When(interest_amount__isnull=False, then=Value("Financial"))
            ),
            about_family=Case(
                When(family_member_name__isnull=False, then=Value("Family")),
            ),
            other_category=Case(
                When(interest_amount__isnull=True, family_member_name__isnull=True,
                    then=Value("Other"))
            )
        )
        .values(
            "id",
            "member_of_parliament__name",
            "category_name",
            "date_created",
            "interest_summary",
            "interest_currency",
            "interest_amount",
            "has_financial",
            "about_family",
            "other_category"
        )
    )

    paginator = Paginator(registered_interests, 50)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    context = {"registered_interests": page_obj}

    return render(request, "members_interest_app/registered-interests.html", context)


def registered_interest_profile(request, pk):
    registered_interest_profile = get_object_or_404(RegisteredInterest, pk=pk)
    context = {"registered_interest_profile": registered_interest_profile}
    return render(request, "members_interest_app/registered-interest-profile.html", context)