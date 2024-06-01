from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def index(request):
    return render(request, 'members_interest_app/index.html')
def members_of_parliament(request):
    return render(request, 'members_interest_app/members-of-parliament.html')