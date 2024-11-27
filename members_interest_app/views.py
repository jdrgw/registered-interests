from collections import (
    Counter,  # noqa: F401, had intended to use with spacy to implement ml but leaving here
)

# import spacy
from django.core.paginator import Paginator
from django.db.models import Case, Count, Q, Sum, Value, When
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
        "house__name",
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
        RegisteredInterest.objects.annotate(
            # Financial Interests
            has_financial=Case(
                When(interest_amount__isnull=False, then=Value("Financial"))
            ),
            # Family-Related Interests
            about_family=Case(
                When(
                    Q(family_member_name__isnull=False)
                    | Q(family_member_paid_by_mp_or_parliament=True)
                    | Q(family_member_lobbies=True),
                    then=Value("Family"),
                ),
            ),
            # Employment-Related Interests
            about_employment=Case(
                When(
                    Q(role__isnull=False) | Q(employer_name__isnull=False),
                    then=Value("Employment"),
                )
            ),
            # Other Interests
            other_category=Case(
                When(
                    Q(interest_amount__isnull=True)
                    & Q(family_member_name__isnull=True)
                    & Q(family_member_paid_by_mp_or_parliament__isnull=True)
                    & Q(family_member_lobbies__isnull=True)
                    & Q(role__isnull=True)
                    & Q(employer_name__isnull=True),
                    then=Value("Other"),
                )
            ),
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
            "about_employment",
            "other_category",
        )
        .order_by(
            "-date_created",  # Newest records first
            "member_of_parliament__name",  # Then grouped by MP name
            "category_name",  # Then grouped by category
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
    return render(
        request, "members_interest_app/registered-interest-profile.html", context
    )


def stats(request):
    top_10_mps_by_num_interests = (
        MemberOfParliament.objects.annotate(
            num_registered_interests=Count("registeredinterest")
        )
        .values("id", "name", "num_registered_interests")
        .order_by("-num_registered_interests")
    )[:10]

    top_10_mps_by_gbp_interest_sum = (
        MemberOfParliament.objects.filter(
            registeredinterest__gbp_interest_amount__isnull=False
        )  # Filter out NULLs
        .annotate(
            sum_registered_interests=Sum("registeredinterest__gbp_interest_amount")
        )
        .values("id", "name", "sum_registered_interests")
        .order_by("-sum_registered_interests")  # Reverse order for descending sums
    )[:10]

    category_frequency = (
        RegisteredInterest.objects.values("category_name")
        .annotate(cat_freq=Count("category_name"))
        .order_by("-cat_freq")
    )

    context = {
        "top_10_mps_by_num_interest_counts": top_10_mps_by_num_interests,
        "top_10_mps_by_gbp_interest_sum": top_10_mps_by_gbp_interest_sum,
        "category_frequency": category_frequency,
    }

    # # Identify the most frequent keywords and named entities across all summaries.
    # # TODO: figure out alternative as this is v. computationally heavy and will reudce site performance.
    # # TODO: remove following notes

    # nlp.max_length = 2500000
    # nlp = spacy.load("en_core_web_sm")

    # all_summaries = RegisteredInterest.objects.all().values_list("interest_summary", flat=True)
    # agg_summaries = "".join(all_summaries)
    # doc = nlp(agg_summaries)

    # entities = [ent.text for ent in doc.ents]
    # entity_counts = Counter(entities)

    # print("Top Entities:", entity_counts.most_common(10))

    # Alternatives
    # Focus on NORP entities, which represent nationalities, religious groups, and political groups
    # entities = [ent.text for ent in doc.ents if ent.label_ == "NORP"]
    # entity_counts = Counter(entities)

    # Focus on people
    # entities = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    # entity_counts = Counter(entities)

    # Focus on people
    # entities = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    # entity_counts = Counter(entities)

    return render(request, "members_interest_app/stats.html", context)
