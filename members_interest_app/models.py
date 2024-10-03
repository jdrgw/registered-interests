from django.db import models
from django.core.exceptions import ValidationError

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
        default=1  # ID of the "Unknown" House
    )


    def __str__(self):
        return f"{self.name}, {self.house}, {self.constituency}"
    
    def clean(self):
        # check if api_id
        api_id_exists = (
            MemberOfParliament
            .objects
            .filter(api_id=self.api_id)
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