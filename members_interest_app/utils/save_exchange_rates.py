import pandas as pd
from django.db import transaction

from members_interest_app.models import ExchangeRate

# historical currency exchange rates (2009-2024) were downloaded to CSVs using the following URLs:
# https://wwwtest.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp?Travel=NIxAZxSUx&FromSeries=1&ToSeries=50&DAT=RNG&FD=1&FM=Jan&FY=2009&TD=31&TM=Dec&TY=2025&FNY=Y&CSVF=TT&html.x=66&html.y=26&SeriesCodes=XUDLERS&UsingCodes=Y&Filter=N&title=XUDLERS&VPD=Y
# https://wwwtest.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp?Travel=NIxAZxSUx&FromSeries=1&ToSeries=50&DAT=RNG&FD=1&FM=Jan&FY=2009&TD=31&TM=Dec&TY=2025&FNY=Y&CSVF=TT&html.x=66&html.y=26&SeriesCodes=XUDLADS&UsingCodes=Y&Filter=N&title=XUDLADS&VPD=Y
# https://wwwtest.bankofengland.co.uk/boeapps/database/fromshowcolumns.asp?Travel=NIxAZxSUx&FromSeries=1&ToSeries=50&DAT=RNG&FD=1&FM=Jan&FY=2009&TD=31&TM=Dec&TY=2025&FNY=Y&CSVF=TT&html.x=66&html.y=26&SeriesCodes=XUDLGBD&UsingCodes=Y&Filter=N&title=XUDLGBD&VPD=Y


def save_exchange_rates():
    """
    Open static csvs containing Bank of England foreign exchange rate data (for GBP to EUR, AUD, and USD), process the data,
    and save to the ExchangeRate model.

    See function file for links to data sources.
    """
    daily_aud_to_gbp = pd.read_csv("data/exchange_rates/static_bank_of_england_daily_rates/XUDLADS  Bank of England  Database-daily-australian-dollar-to-sterling-fx-since-09.csv")
    daily_eur_to_gbp = pd.read_csv("data/exchange_rates/static_bank_of_england_daily_rates/XUDLERS  Bank of England  Database-daily-euro-to-sterling-fx-since-09.csv")
    daily_gbp_to_usd = pd.read_csv("data/exchange_rates/static_bank_of_england_daily_rates/XUDLGBD  Bank of England  Database-daily-sterling-to-usd-fx-since-09.csv")

    # rename cols 
    daily_aud_to_gbp.columns = ["date", "aud_gbp_daily_spot_price"]
    daily_eur_to_gbp.columns = ["date", "eur_gbp_daily_spot_price"]
    daily_gbp_to_usd.columns = ["date", "gbp_usd_daily_spot_price"]

    # GBP must be the base (cost of currencies in GBP). GBP to USD is correct, but AUD and EUR are base rates, so need to invert them.
    daily_aud_to_gbp["gbp_aud_daily_spot_price"] = 1/daily_aud_to_gbp["aud_gbp_daily_spot_price"]
    daily_eur_to_gbp["gbp_eur_daily_spot_price"] = 1/daily_eur_to_gbp["eur_gbp_daily_spot_price"]

    currency_conversions = (
        daily_gbp_to_usd
        .merge(daily_aud_to_gbp[["date", "gbp_aud_daily_spot_price"]], how="left", on="date")
        .merge(daily_eur_to_gbp[["date", "gbp_eur_daily_spot_price"]], how="left", on="date")
    )

    # Rename cols to currencies for melting dataframe
    currency_conversions.columns = ['date', 'USD', 'AUD', 'EUR']

    # melt dataframe to match ExchangeRate model's structure
    currency_conversions_long = currency_conversions.melt(
        id_vars=["date"], 
        var_name="currency", 
        value_name="rate_to_gbp"
    )

    # make dates datetime objects - db field is DateField but django can parse datetime objects to dates
    currency_conversions_long["date"] = pd.to_datetime(currency_conversions_long["date"], format="%d %b %y")

    try:
        with transaction.atomic():
            
            instances=[]
            tuples = currency_conversions_long.itertuples()
            
            for tuple in tuples:
                instances.append(
                    ExchangeRate(
                        date=tuple.date,
                        currency=tuple.currency,
                        rate_to_gbp=tuple.rate_to_gbp
                    )
                )
            
            ExchangeRate.objects.bulk_create(instances)
            
            print(len(instances))
    except Exception as e:
        print(e)