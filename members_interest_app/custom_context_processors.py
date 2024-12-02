from .forms import SearchForm


def search_form_context(request):
    return {'form': SearchForm()}