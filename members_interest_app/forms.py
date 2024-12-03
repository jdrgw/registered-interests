from django import forms


class SearchForm(forms.Form):
    q = forms.CharField(
        label="q",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-control me-2",
                "placeholder": "Search",
                "aria-label": "Search",
            }
        ),
    )
