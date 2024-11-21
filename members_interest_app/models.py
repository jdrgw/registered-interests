from django.core.exceptions import ValidationError
from django.db import models


class House(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return f"{self.name}"


# Create your models here.
class MemberOfParliament(models.Model):
    id = models.AutoField(primary_key=True)

    # MP data
    api_id = models.CharField(max_length=255, unique=True, null=False)
    name = models.CharField(max_length=350, null=False)
    gender = models.CharField(max_length=255, null=True)
    thumbnail_url = models.URLField(max_length=300, blank=True)

    # Seat data
    constituency = models.CharField(max_length=255, null=True)
    membership_start = models.DateTimeField(null=True)
    membership_end = models.DateTimeField(null=True)
    membership_end_reason = models.CharField(max_length=255, null=True)
    membership_end_notes = models.TextField(null=True)
    house = models.ForeignKey(
        "House",
        on_delete=models.PROTECT,
        null=False,
        default=1,  # ID of the "Unknown" House
    )

    def __str__(self):
        return f"{self.name}, {self.house}, {self.constituency}"

    def clean(self):
        # check if api_id
        api_id_exists = (
            MemberOfParliament.objects.filter(api_id=self.api_id)
            .exclude(pk=self.pk)
            .exists()
        )

        if api_id_exists:
            raise ValidationError(
                f"A Member of Parliament with the api_id '{self.api_id}' already exists"
            )

    def save(self, *args, **kwargs):
        # Call the clean method to ensure validation is applied
        self.clean()
        super().save(*args, **kwargs)


# TODO: split registered interest into separate models based on category type in API data. Bunging into one model for speed.
class RegisteredInterest(models.Model):
    id = models.AutoField(primary_key=True)
    member_of_parliament = models.ForeignKey(
        MemberOfParliament, on_delete=models.CASCADE, null=False, to_field="api_id"
    )

    # fields from api
    api_id = models.CharField(
        max_length=255, unique=False, null=False
    )  # api_id non-unique
    unique_api_generated_id = models.CharField(
        max_length=255, unique=True, null=False
    )  # api_id non-unique – create from count of api_id-member_id pairing
    category_id = models.CharField(max_length=255, null=False)
    category_name = models.CharField(max_length=255, null=False)
    sort_order = models.CharField(max_length=255, null=False)
    interest_summary = models.TextField(null=True, blank=False)
    date_created = models.DateTimeField(null=False)
    date_last_amended = models.DateTimeField(
        null=True
    )  # sometimes absent in API data (25%)
    date_deleted = models.DateTimeField(
        null=True, blank=True
    )  # Allowing null for non-deleted entries
    is_correction = models.BooleanField(default=False)
    is_child_interest = models.BooleanField(default=False)
    parent_interest = models.CharField(max_length=25, null=True, blank=True)

    # fields where data to be extracted from api_data
    interest_amount = models.DecimalField(
        null=True, blank=True, decimal_places=2, max_digits=12
    )
    CURRENCY_CHOICES = (
        ("GBP", "Pound Sterline"),
        ("USD", "US Dollar"),
        ("EUR", "Euro"),
        ("AUD", "Australian Dollar"),
    )
    interest_currency = models.CharField(
        max_length=50, null=True, blank=True, choices=CURRENCY_CHOICES
    )
    number_of_extracted_amounts = models.IntegerField(null=True, blank=True)
    contains_loan = models.BooleanField(null=True, blank=True)
    contains_time_period = models.BooleanField(
        null=True, blank=True
    )  # some entries contain values per <event>/<time period>, this flag indicates quality issues
    payer = models.CharField(max_length=255, null=True, blank=True)
    PAYER_TYPE_CHOICES = (
        ("person", "person"),
        ("company", "company"),
        ("unknown", "unknown"),
    )
    payer_type = models.CharField(
        max_length=255, null=True, blank=True, choices=PAYER_TYPE_CHOICES
    )
    payer_address = models.TextField(null=True, blank=True)
    payer_companies_house_id = models.CharField(max_length=10, null=True, blank=True)
    purpose = models.TextField(null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)
    employer_name = models.CharField(max_length=255, null=True, blank=True)
    family_member_name = models.CharField(max_length=255, null=True, blank=True)
    family_member_relationship = models.CharField(max_length=255, null=True, blank=True)
    family_member_role = models.CharField(max_length=255, null=True, blank=True)
    family_member_paid_by_mp_or_parliament = models.BooleanField(null=True, blank=True)
    family_member_lobbies = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"{self.category_name} - {self.interest_summary}"
