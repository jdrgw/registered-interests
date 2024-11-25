from django.db.models.functions import TruncDate

from members_interest_app.models import ExchangeRate, RegisteredInterest


def convert_interest_amount_to_gbp():
    """
    Updates the gbp_interest_amount field for all RegisteredInterest instances in bulk.
    """
    interests_to_update = []
    interests = RegisteredInterest.objects.all()

    for interest in interests:
        if not interest.interest_amount or not interest.interest_currency:
            continue  # Skip if there's no amount or currency specified

        if interest.interest_currency == "GBP":
            # If currency is already GBP, use the interest amount directly
            interest.gbp_interest_amount = interest.interest_amount
        else:
            # Match exchange rate based on interest date
            exchange_rate = ExchangeRate.objects.filter(
                currency=interest.interest_currency,
                date__lte=interest.date_created.date()  # Truncate datetime to date
            ).order_by("-date").first()  # Get the latest exchange rate before or on the date

            if exchange_rate:
                # Convert to GBP using the exchange rate
                interest.gbp_interest_amount = interest.interest_amount * exchange_rate.rate_to_gbp
            else:
                # No matching exchange rate; set as None (optional)
                interest.gbp_interest_amount = None

        # Add to the list for bulk update
        interests_to_update.append(interest)

    # Bulk update only the gbp_interest_amount field
    if interests_to_update:
        RegisteredInterest.objects.bulk_update(
            interests_to_update, ["gbp_interest_amount"]
        )

    updated_count = len(interests_to_update)
    message = f"GBP interest amounts updated successfully in bulk for {updated_count} records."
    print(message)

    return message
