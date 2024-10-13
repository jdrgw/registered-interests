from django.shortcuts import render, get_object_or_404
from .models import MemberOfParliament
from django.core.paginator import Paginator

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
