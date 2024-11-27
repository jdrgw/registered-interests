import csv
import json
import os
import re
import textwrap
from collections import defaultdict

import numpy as np
import pandas as pd
from dateutil import parser
from django.db import models, transaction
from django.db.models.fields import CharField
from django.utils import timezone

from members_interest_app.models import MemberOfParliament, RegisteredInterest

# TODO: lots of this could be improved and streamlined, see further todos

# TODO: make docstrings style uniform

# TODO: unsure these category list constants are necessary, possible to incorporate into function where used.
CATEGORIES_WITH_EASILY_EXTRACTABLE_AMOUNTS = [
    "2. (a) Support linked to an MP but received by a local party organisation or indirectly via a central party organisation",
    "2. (b) Any other support not included in Category 2(a)",
    "3. Gifts, benefits and hospitality from UK sources",
    "8. Miscellaneous",
    "Category 6: Sponsorship",
    "Category 8: Gifts, benefits and hospitality",
    "Category 9: Miscellaneous financial interests",
]

CATEGORIES_AMOUNTS_EXTRACTABLE_WITH_PROCESSING = [
    "1. Employment and earnings",
    "4. Visits outside the UK",
    "5. Gifts and benefits from sources outside the UK",
    "Category 10: Non-financial interests (a)",
    "Category 1: Directorships",
    "Category 2: Remunerated employment, office, profession etc.",
]

EXTRACTABLE_AMOUNT_CATEGORIES = (
    CATEGORIES_WITH_EASILY_EXTRACTABLE_AMOUNTS
    + CATEGORIES_AMOUNTS_EXTRACTABLE_WITH_PROCESSING
)

# TODO: think about putting this pattern into function where used; don't think constant is necessary
EXTRACT_MONEY_PATTERN = r"(?:[£$€]?\d{1,3}(?:[,.]\d{1,3})*(?:\.\d{2})?(?:[kKmM]?)(?: ?[A-Z]{2,3})?|(?:[A-Z]{2,3} ?[£$€]?\d{1,3}(?:[,.]\d{3})*(?:\.\d{2})?))"


def extract_data_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file at {file_path} does not exist.")

    with open(file_path, "r") as f:
        read_file = f.read()
        json_objs = [obj for obj in read_file.split("\n\n\n") if obj.strip()]
        parsed_json_objs = [json.loads(obj) for obj in json_objs]
        rows_w_values = [row for row in parsed_json_objs if row.get("value")]
        return rows_w_values


def extract_member_id(links):
    """
    Extracts the member ID from a list of dictionaries.

    Parameters:
        links (list of dict): A list of link dictionaries, each containing
                              'rel' and 'href' keys.

    Returns:
        int or None: The extracted member ID if found; otherwise, None.
    """

    if not isinstance(links, list):
        raise ValueError("Expected a list of links.")

    for link in links:
        if not isinstance(link, dict) or "rel" not in link or "href" not in link:
            raise ValueError(
                "Each link must be a dictionary with 'rel' and 'href' keys."
            )

        if link["rel"] == "self":
            match = re.search(r"/Members/(\d+)/", link["href"])
            if match:
                return int(match.group(1))
    return None


def flatten_interests_to_df(dataset):
    """
    Flattens a nested dataset of member interests into a DataFrame.

    This function takes a dataset of members and their categorised interests,
    and returns a flattened DataFrame with one row per interest
    (including child interests).

    Parameters:
        dataset (list of dict): A list of dictionaries, each containing member
                                links and categorised interest information.

    Returns:
        pd.DataFrame: A DataFrame with flattened interest data.
    """

    if not isinstance(dataset, list):
        raise ValueError("flatten_interests_to_df expects a list.")

    flattened_data = []
    interest_count = defaultdict(lambda: defaultdict(int))  # Count for main interests
    child_interest_count = defaultdict(
        lambda: defaultdict(int)
    )  # Count for child interests

    for entry in dataset:
        if not isinstance(entry, dict):
            raise TypeError("Each entry must be a dictionary.")
        member_id = extract_member_id(entry["links"])

        for category in entry["value"]:
            category_id = category["id"]
            category_name = category["name"]
            sort_order = category["sortOrder"]

            for interest in category["interests"]:
                if not isinstance(interest, dict):
                    raise TypeError("Each interest must be a dictionary.")

                # Handle main interests
                # Following code generates a unique id for interests, which seem non-unique.
                # TODO: code generating uniqueInterestId is duplicated across main and child interests, fix this.
                interest_id = interest["id"]
                interest_count[member_id][interest_id] += 1
                count = interest_count[member_id][interest_id]
                interest_count_str = f"{member_id}-{interest_id}-{count}"

                flattened_data.append(
                    {
                        "memberId": member_id,
                        "categoryId": category_id,
                        "categoryName": category_name,
                        "sortOrder": sort_order,
                        "interestId": interest_id,
                        "uniqueInterestId": interest_count_str,
                        "interest": interest["interest"],
                        "createdWhen": interest["createdWhen"],
                        "lastAmendedWhen": interest["lastAmendedWhen"],
                        "deletedWhen": interest["deletedWhen"],
                        "isCorrection": interest["isCorrection"],
                        "isChildInterest": False,  # Main interest
                        "parentInterest": None,
                    }
                )

                # Flatten child interests if they exist
                for child_interest in interest.get("childInterests", []):
                    if not isinstance(child_interest, dict):
                        raise TypeError("Each child interest must be a dictionary.")

                    child_interest_id = child_interest["id"]
                    child_interest_count[member_id][child_interest_id] += 1
                    child_count = child_interest_count[member_id][child_interest_id]
                    child_interest_count_str = (
                        f"{member_id}-{interest_id}-{child_interest_id}-{child_count}"
                    )

                    flattened_data.append(
                        {
                            "memberId": member_id,
                            "categoryId": category_id,
                            "categoryName": category_name,
                            "sortOrder": sort_order,
                            "interestId": child_interest_id,
                            "uniqueInterestId": child_interest_count_str,
                            "interest": child_interest["interest"],
                            "createdWhen": child_interest["createdWhen"],
                            "lastAmendedWhen": child_interest["lastAmendedWhen"],
                            "deletedWhen": child_interest["deletedWhen"],
                            "isCorrection": child_interest["isCorrection"],
                            "isChildInterest": True,
                            "parentInterest": interest_id,
                        }
                    )

    df = pd.DataFrame(flattened_data)

    if df.empty:
        raise ValueError(
            "DataFrame is empty. Something went wrong with flattening registered interest data."
        )

    return df


def col_names_to_snake_case(df):
    """Takes and returns a dataframe, converting column names from camelcase to lowercase snakecase"""

    df.columns = [re.sub(r"(?<!^)(?=[A-Z])", "_", word).lower() for word in df.columns]
    return df


def remove_space_in_registration_numbers(df):
    """Processes 'interest' column to create 'edited_interest', removing spaces in 'registration <number>' patterns."""

    if df["interest"].dtype != "object":
        raise ValueError("All entries in the 'interest' column must be strings.")

    registration_number_pattern = re.compile(
        r"(registration)\s+(\d+)", flags=re.IGNORECASE
    )

    df.loc[:, "edited_interest"] = df["interest"].apply(
        lambda x: registration_number_pattern.sub(
            lambda match: f"{match.group(1)}{match.group(2)}", x
        )
    )
    return df


def convert_abbreviated_numbers_to_numbers(df, column):
    """Convert specific abbreviated monetary values in a DataFrame column to full numbers."""

    # A more elegant regex solution using r"\b\d[.,]?\d*[mMkK]\b" was considered, but specific replacements
    # for just two cases is simpler and avoids false positives (e.g., company names like "3M" and addresses).

    replacements = {
        "£1.2m from Lord Alli": "£1200000 from Lord Alli",
        "excess of £250k": "excess of £250000",
    }

    pattern = "|".join(map(re.escape, replacements.keys()))

    mask = df[column].str.contains(pattern, regex=True)

    if not mask.any():
        raise ValueError(
            "Replacement text not found in the specified column. Something went wrong."
        )

    for old, new in replacements.items():
        df.loc[mask, column] = df.loc[mask, column].str.replace(old, new)

    return df


def filter_currency(amounts):
    "checks if currency symbol or codes (£, $, €, GBP, AUD, EUR) in input"
    symbols = ["£", "€", "$", "GBP", "AUD", "EUR"]
    return [amount for amount in amounts if any(symbol in amount for symbol in symbols)]


def has_multiple_fullstops(amounts):
    """Check if any amount has more than one full stop (indicating non-number e.g. date), and return boolean."""

    if not amounts or not isinstance(amounts, list):
        return False

    for item in amounts:
        # Ensure item is a string
        if isinstance(item, str) and item.count(".") > 1:
            return True

    return False


def extract_max_amount_with_currency(dataframe, column_name):
    """
    Extracts monetary amounts and their currencies from specified column,
    identifies the max amount along with its currency, and returns new columns with
    the split amounts, currencies, and the maximum amount and currency.

    Parameters:
    dataframe (pd.DataFrame): The input DataFrame containing the monetary data.
    column_name (str): The name of the column to extract amounts from.
    """

    if column_name not in dataframe.columns:
        raise KeyError(f"'{column_name}' does not exist in the DataFrame.")

    currency_choice_map = {
        "AUD": "AUD",
        "USD": "USD",
        "GBP": "GBP",
        "EUR": "EUR",
        "$": "USD",
        "£": "GBP",
        "€": "EUR",
    }
    amounts_pattern = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)")
    currencies_pattern = re.compile(r"(AUD|USD|GBP|EUR|£|\$|€)")

    def process_entry(entry_list):
        amount_currency_tuples = []

        for entry in entry_list:
            if not entry:  # Skip empty entries
                continue

            try:
                amounts = amounts_pattern.findall(entry)
                currencies = currencies_pattern.findall(entry)

                for i, amount in enumerate(amounts):
                    clean_amount = float(amount.replace(",", ""))
                    currency = (
                        currency_choice_map.get(currencies[i])
                        if i < len(currencies)
                        else None
                    )
                    amount_currency_tuples.append((clean_amount, currency))

            except (ValueError, IndexError) as e:
                print(f"Error processing entry '{entry}': {e}")
                continue

        # Find the tuple with the maximum amount
        if amount_currency_tuples:
            max_tuple = max(amount_currency_tuples, key=lambda x: x[0])
            max_amount, max_currency = max_tuple
        else:
            max_amount, max_currency = None, None

        # Separate amounts and currencies
        split_amounts = [t[0] for t in amount_currency_tuples]
        split_currencies = [t[1] for t in amount_currency_tuples]

        return split_amounts, split_currencies, max_amount, max_currency

    # Apply inner function to dataframe
    dataframe[
        ["split_amounts", "split_currencies", "max_amount", "max_amount_currency"]
    ] = dataframe[column_name].apply(
        lambda x: pd.Series(
            process_entry(x)
        )  # pd.Series enables population of multiple columns
    )

    return dataframe


def mentions_debt_synonyms(df, col):
    """
    checks whether column contains synonyms for debt and returns a bool in new column
    synonyms:
        debt
        loan
        mortgage

    """
    synonyms = ["debt", "loan", "mortgage"]

    synonyms_pattern = r"\b(?:" + "|".join(synonyms) + r")\b"

    df["contains_debt_synonym"] = df[col].str.contains(
        synonyms_pattern, regex=True, flags=re.IGNORECASE
    )

    return df


def mentions_time_period_or_preposition(df, col):
    """
    returns bool if column contains (or doesn't) following time periods or time prepositions
        per
        day
        month
        year
        annual
        daily
        monthly
        yearly
        annually

    Presence indicates amounts extracted should have low confidence as these aren't accounted for.

    """

    time_periods_or_prepositions = [
        "per",
        "day",
        "month",
        "year",
        "annual",
        "daily",
        "monthly",
        "yearly",
        "annually",
    ]

    time_periods_or_prepositions_pattern = (
        r"\b(?:" + "|".join(time_periods_or_prepositions) + r")\b"
    )

    df["contains_time_periods_and_prepositions"] = df[col].str.contains(
        time_periods_or_prepositions_pattern, regex=True, case=False
    )

    return df


def extract_payer_details(df):
    """
    Extracts donor details from the interest, including donor name, donor type, donor address,
    and Companies House ID using regex and returns a new dataframe with the extracted information.

    Returns:
    Original dataframe with four new columns:
        - 'donor_name': Extracted donor or payer name.
        - 'donor_type': Type of donor (individual or company).
        - 'donor_address': Address of the donor.
        - 'companies_house_id': Companies House registration ID.
    """

    # TODO: fix donor name pattern picking up on "donor name, some address" patterns
    donor_name_pattern = r"(?<!Address of )(?:donor|payer):\s?([\w\s,]+)(?=\r\n|$)"
    donor_type_pattern = r"Donor status:\s(\w+(?:\s\w+)*)(?=\r?\n|$)"
    donor_address_pattern = r"Address of donor:\s?([^\r\n\.]*)(?=[\r\n\.])"
    companies_house_id_pattern = r"(?:registration)\s+(\d+)"

    df["donor_name"] = df["interest"].apply(
        lambda x: re.search(donor_name_pattern, x).group(1)
        if re.search(donor_name_pattern, x)
        else None
    )
    df["donor_type"] = df["interest"].apply(
        lambda x: re.search(donor_type_pattern, x).group(1)
        if re.search(donor_type_pattern, x)
        else None
    )
    df["donor_address"] = df["interest"].apply(
        lambda x: re.search(donor_address_pattern, x).group(1)
        if re.search(donor_address_pattern, x)
        else None
    )
    df["companies_house_id"] = df["interest"].apply(
        lambda x: re.search(companies_house_id_pattern, x).group(1)
        if re.search(companies_house_id_pattern, x)
        else None
    )

    return df


def extract_mp_role_and_employer(df):
    """
    Extracts MP role and employer information into "mp_role" and "employer_name" columns
    in the input DataFrame and returns the modified DataFrame.

    - For rows where `category_name` is exactly "1. Employment and earnings" and `donor_name` is not null,
      `donor_name` is assigned to `employer_name`, and `mp_role` is extracted from `interest` using
      the pattern `r"(?:[wW]ork or services: )(.*)(?:\r)"`.

    - For rows where `category_name` matches specific categories in `other_categories_with_employer_data`,
      extracts text after the first comma in `interest` to `employer_name` and assigns text before the
      first comma to `mp_role`.

    Parameters:
    ----------
    df : pandas.DataFrame
        DataFrame with `category_name`, `donor_name`, and `interest` columns.

    Returns:
    -------
    pandas.DataFrame
        DataFrame with added `mp_role` and `employer_name` columns containing extracted information.
    """

    # Pattern for extracting role from "1. Employment and earnings" category
    pattern = r"(?:[wW]ork or services: )(.*)(?:\r)"

    # Define mask for exact match with "1. Employment and earnings" and non-null donor_name
    employment_earnings_mask = (
        df["category_name"] == "1. Employment and earnings"
    ) & df["donor_name"].notnull()

    # Define mask for other specific categories
    other_categories_with_employer_data = [
        "Category 2: Remunerated employment, office, profession etc.",
        "Category 10: Non-financial interests (a)",
        "Category 10: Non-financial interests (b)",
        "Category 10: Non-financial interests (c)",
        "Category 10: Non-financial interests (d)",
        "Category 10: Non-financial interests (e)",
        "Category 1: Directorships",
    ]
    other_categories_mask = df["category_name"].isin(
        other_categories_with_employer_data
    )

    df.loc[employment_earnings_mask, "employer_name"] = df["donor_name"]

    df.loc[employment_earnings_mask, "mp_role"] = df["interest"].str.extract(
        pattern, expand=False
    )

    df.loc[other_categories_mask, "employer_name"] = (
        df["interest"].str.split(",", n=1).str.get(1)
    )

    df.loc[other_categories_mask, "mp_role"] = (
        df["interest"].str.split(",", n=1).str.get(0)
    )

    return df


def extract_family_member_info(df):
    """
    Filters and extracts family member details from the 'interest' column, including family member name,
    relationship, role, and whether they are paid by MP or Parliament, for specified categories.


    Returns:
    A new dataframe containing only rows from the specified categories, with added columns:
        - 'family_member_name': Name of the family member.
        - 'family_member_relationship': Relationship of the family member.
        - 'family_member_role': Role of the family member.
        - 'family_member_paid_by_mp_or_parliament': Boolean indicating if paid by MP/Parliament.
    """

    family_categories = [
        "10. Family members engaged in lobbying the public sector on behalf of a third party or client",
        "9. Family members employed and paid from parliamentary expenses",
    ]

    filtered_df = df[df["category_name"].isin(family_categories)].copy()

    name_pattern = r"Name:\s*(.*?)\r"
    relationship_pattern = r"Relationship:\s*(.*?)\r"
    role_pattern = r"Role:\s*(.*?)\r"

    filtered_df["family_member_name"] = filtered_df["interest"].apply(
        lambda x: re.search(name_pattern, x).group(1)
        if re.search(name_pattern, x)
        else None
    )
    filtered_df["family_member_relationship"] = filtered_df["interest"].apply(
        lambda x: re.search(relationship_pattern, x).group(1)
        if re.search(relationship_pattern, x)
        else None
    )
    filtered_df["family_member_role"] = filtered_df["interest"].apply(
        lambda x: re.search(role_pattern, x).group(1)
        if re.search(role_pattern, x)
        else None
    )

    filtered_df["family_member_paid_by_mp_or_parliament"] = False
    filtered_df.loc[
        filtered_df["category_name"]
        == "9. Family members employed and paid from parliamentary expenses",
        "family_member_paid_by_mp_or_parliament",
    ] = True

    filtered_df["family_member_lobbies"] = False
    filtered_df.loc[
        filtered_df["category_name"]
        == "9. Family members employed and paid from parliamentary expenses",
        "family_member_lobbies",
    ] = True

    return filtered_df


def validate_columns(df):
    "Raise an error if dataframe column names are unexpected, which could disrupt named access during database inserts"

    expected_cols = [
        "member_id",
        "category_id",
        "category_name",
        "sort_order",
        "interest_id",
        "unique_interest_id",
        "interest",
        "created_when",
        "last_amended_when",
        "deleted_when",
        "is_correction",
        "is_child_interest",
        "parent_interest",
        "contains_time_periods_and_prepositions",
        "contains_debt_synonym",
        "split_amounts",
        "max_amount_currency",
        "max_amount",
        "filtered_amounts",
        "has_multiple_fullstops",
        "extracted_amounts",
        "split_currencies",
        "edited_interest",
        "donor_name",
        "donor_type",
        "donor_address",
        "companies_house_id",
        "family_member_relationship",
        "family_member_paid_by_mp_or_parliament",
        "family_member_name",
        "family_member_lobbies",
        "family_member_role",
        "employer_name",
        "mp_role",
    ]

    if list(df.columns) != expected_cols:
        message = textwrap.dedent(f"""\
            Column order mismatch: the DataFrame's columns do not match the expected order.
            This misalignment could lead to incorrect data being saved to the wrong database fields,
            resulting in potential data integrity issues.

            Expected columns:
            {expected_cols}

            Actual columns:
            {list(df.columns)}
        """)
        raise ValueError(message)


def parse_and_format_dates(value):
    """
    Standardise datetime format, remove milliseconds.
    """
    try:
        if pd.isna(value):
            return None

        # Try to parse the string as a datetime object
        parsed_date = parser.parse(value)

        # Remove milliseconds by replacing the microseconds to zero
        parsed_date = parsed_date.replace(microsecond=0)

        return parsed_date
    except (ValueError, TypeError):
        # If parsing fails, return NaT or None
        return np.NaN


def make_dates_aware(value):
    "Takes a datetime object and makes it aware or returns None if None or NaT"
    if value is not None and not pd.isna(value):
        if timezone.is_naive(value):
            return timezone.make_aware(
                value, timezone.utc
            )  # Convert naive to aware in UTC
        else:
            return value.astimezone(
                timezone.utc
            )  # Convert aware datetime to UTC if it's already aware
    return None


def bulk_save_data(df, batch_size=5000):
    """
    Batch the dataframe and bulk save the batches to the database.
    Log exceptions in a custom file on top of django's logging infrastructure to
    make finding and analysing them easier.
    """

    # Prepare error logging setup – logging exists, but want to use self contained file for ease
    errors = []
    error_repo = os.path.abspath(os.path.join(__file__, "../../../.."))
    error_file = os.path.join(error_repo, "errors.csv")

    # Calculate dataset shape and processing metadata to handle unequal sized batches
    total_rows = len(df)
    n_batches = total_rows // batch_size + 1  # Adjust for last small batch
    last_batch_size = total_rows % batch_size

    # Setup for saving DataFrame rows in batches
    tuples = df.itertuples(index=False, name="Row")
    batch = []
    records_created = 0

    # set up dict of all current members to assign member object to each member_of_parliament field
    members = MemberOfParliament.objects.all()
    members_dict = {member.api_id: member for member in members}

    try:
        with transaction.atomic():
            for idx, tup in enumerate(tuples):
                # Build a dictionary of model fields with values from DataFrame row
                instance_data = {
                    field: getattr(tup, field)
                    for field in df.columns
                    if hasattr(tup, field)
                }

                cleaned_instance_data = {
                    key: None
                    if pd.isna(value)
                    and isinstance(RegisteredInterest._meta.get_field(key), CharField)
                    else value
                    for key, value in instance_data.items()
                }

                # Replace member_of_parliament field in instance_data with MemberOfParliament object
                cleaned_instance_data["member_of_parliament"] = members_dict.get(
                    str(cleaned_instance_data["member_of_parliament"])
                )

                # make dates timezone aware
                cleaned_instance_data["date_created"] = make_dates_aware(
                    cleaned_instance_data["date_created"]
                )
                cleaned_instance_data["date_last_amended"] = make_dates_aware(
                    cleaned_instance_data["date_last_amended"]
                )
                cleaned_instance_data["date_deleted"] = make_dates_aware(
                    cleaned_instance_data["date_deleted"]
                )

                # Replace interest_amount NaN's with None to accomodate db field requirements
                cleaned_instance_data["interest_amount"] = (
                    None
                    if pd.isna(cleaned_instance_data["interest_amount"])
                    else cleaned_instance_data["interest_amount"]
                )

                # Create an instance of RegisteredInterest with the extracted data
                instance = RegisteredInterest(**cleaned_instance_data)
                batch.append(instance)

                # Calculate the current batch number based on the index and batch size
                current_batch_number = idx // batch_size + 1

                # Check if the batch is full or if we are on the final batch and that is full
                if len(batch) == batch_size or (
                    current_batch_number == n_batches and len(batch) == last_batch_size
                ):
                    try:
                        RegisteredInterest.objects.bulk_create(batch)
                        records_created += len(batch)
                        batch = []  # Clear the batch after saving
                    except Exception as e:
                        message = f"{type(e).__name__} during bulk create: {str(e)}"
                        errors.append([message])

        # After the loop, check if there were any errors and raise an exception to rollback all changes
        if errors:
            records_created = 0
            raise Exception(
                "Errors occurred during bulk save, all transactions rolled back."
            )

    except Exception as global_error:
        # Collect global errors outside the transaction block
        global_error_message = (
            f"{type(global_error).__name__} during transaction: {str(global_error)}"
        )
        errors.append([global_error_message])

    # Write errors to the CSV file
    with open(error_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Error Message"])  # CSV header
        writer.writerows(errors)

    # Return the number of records successfully created
    return records_created


# TODO: bulk save function formats some types due to making df values saveable, so this function could be made obsolete
def check_and_adjust_column_types(dataframe: pd.DataFrame, model: models.Model):
    "check that column data types in the dataframe's match database field types and if not update the data types"

    model_fields = {
        field.name: field.get_internal_type() for field in model._meta.fields
    }
    df_types = dataframe.dtypes.apply(lambda x: str(x)).to_dict()

    mismatched_columns = []

    # Map Django field types to pandas types
    django_to_pandas = {
        "CharField": "object",
        "TextField": "object",
        "IntegerField": "int64",
        "FloatField": "float64",
        "BooleanField": "bool",
        "DateField": "datetime64[ns]",
        "DateTimeField": "datetime64[ns]",
        "DecimalField": "float64",
        # Add more field types as needed
    }

    for column, df_type in df_types.items():
        model_type = model_fields.get(column)
        if model_type:
            expected_type = django_to_pandas.get(model_type)
            if expected_type and df_type != expected_type:
                mismatched_columns.append((column, df_type, expected_type))

    if mismatched_columns:
        print("Found mismatched column types:")
        for col, df_t, expected_t in mismatched_columns:
            print(
                f"  Column '{col}' has dtype '{df_t}', but expected '{expected_t}' based on model field."
            )

        # Prompt user to adjust the types
        adjust = ""
        while adjust not in ["y", "n"]:
            adjust = (
                input(
                    "\nWould you like to automatically adjust the column types to match the model? (y/n): "
                )
                .strip()
                .lower()
            )

        if adjust == "y":
            for col, df_t, expected_t in mismatched_columns:
                # Adjust the column type in the DataFrame
                if expected_t == "object":
                    dataframe[col] = dataframe[col].astype(str)
                elif expected_t == "int64":
                    dataframe[col] = pd.to_numeric(
                        dataframe[col], errors="coerce", downcast="integer"
                    )
                elif expected_t == "float64":
                    dataframe[col] = pd.to_numeric(
                        dataframe[col], errors="coerce", downcast="float"
                    )
                elif expected_t == "bool":
                    dataframe[col] = dataframe[col].fillna(False).astype(bool)
                elif expected_t == "datetime64[ns]":
                    dataframe[col] = pd.to_datetime(dataframe[col], errors="coerce")

            print("\nColumn types have been adjusted.")
    else:
        print("All DataFrame columns match the model field types.")

    return mismatched_columns


def truncate_strings_to_max_length(df, model=RegisteredInterest):
    """
    Truncates string values in the dataframe that exceed the maximum length specified in the model's CharField.

    This function checks the length of string fields in the dataframe against their corresponding model's `max_length` attribute
    (from the `CharField`). If the string exceeds the maximum length, it is truncated to fit within the allowed length.
    This is a simple, blunt validation and modification process, which may result in loss of data where truncation occurs.

    Returns:
    pandas.DataFrame: The modified dataframe with truncated string values where necessary.
    """

    for field in RegisteredInterest._meta.fields:
        field_name = field.name
        field_type = field.get_internal_type()
        field_max_len = field.max_length

        try:
            if field_name in df.columns and field_type == "CharField":
                # Directly apply truncation for strings exceeding max length
                exceeds_max_length_mask = df[field_name].str.len() > field_max_len
                df[field_name] = df[field_name].where(
                    ~exceeds_max_length_mask, df[field_name].str[:field_max_len]
                )
        except AttributeError as e:
            # Catch the error when .str is not applicable
            print(f"Error when processing column '{field_name}': {e}")

            # Identify problematic rows
            problematic_rows = df[~df[field_name].apply(lambda x: isinstance(x, str))]
            print(f"Problematic rows in column '{field_name}':")
            print(problematic_rows)

            return problematic_rows

    return df


# Stage 1: get file and extract, flatten and preprocess data, returning dataframe
def extract_preprocess_interest_data(file_path):
    "Takes filepath and combines functions that extract data from named JSON file, store it in dataframe then format dataframe"

    data = extract_data_from_file(file_path)
    data = flatten_interests_to_df(data)
    data = col_names_to_snake_case(data)
    return data


# stage 2: extract currencies, amounts, n amounts
def extract_currencies_and_amounts(df):
    """
    Take dataframe and combines functions to extract currencies, amounts and financial data
    from registered interests and store in dataframe. Returns dataframe.
    """

    # return bool if interest contains time period or time preposition to indicate to indicate data quality
    # Presence indicates amounts extracted should have low confidence as these aren't accounted for
    df = mentions_time_period_or_preposition(df, "interest")

    # return bool if interest contains debt synonym
    df = mentions_debt_synonyms(df, "interest")

    # create slice containing rows where currencies and amounts are extractable for efficieny extraction
    data_w_extractable_amts = df[
        df["category_name"].isin(EXTRACTABLE_AMOUNT_CATEGORIES)
    ].copy()

    data_w_extractable_amts = remove_space_in_registration_numbers(
        data_w_extractable_amts
    )
    data_w_extractable_amts = convert_abbreviated_numbers_to_numbers(
        data_w_extractable_amts, "edited_interest"
    )

    # extract currency and amounts from edited_interest – pattern also returns some normal/other numbers
    data_w_extractable_amts["extracted_amounts"] = data_w_extractable_amts[
        "edited_interest"
    ].apply(lambda x: re.findall(EXTRACT_MONEY_PATTERN, x))

    # filter extracted_amounts for genuine currencies and amounts
    data_w_extractable_amts["filtered_amounts"] = data_w_extractable_amts[
        "extracted_amounts"
    ].apply(filter_currency)

    # check if filtered amounts contains more than one full stop (implies not real amount e.g. date) and filter out if true
    data_w_extractable_amts["has_multiple_fullstops"] = data_w_extractable_amts[
        "filtered_amounts"
    ].apply(has_multiple_fullstops)
    if data_w_extractable_amts["has_multiple_fullstops"].any():
        print(
            "Some amounts have multiple full stops, implying non-amounts are still present; check this."
        )
        data_w_extractable_amts = data_w_extractable_amts[
            data_w_extractable_amts["has_multiple_fullstops"] == True  # noqa: E712
        ]

    # split and extract filtered amounts and currencies and extract max amount with its currency
    # convert amounts to floats in operation
    data_w_extractable_amts = extract_max_amount_with_currency(
        data_w_extractable_amts, "filtered_amounts"
    )

    new_cols = set(data_w_extractable_amts.columns) - set(df.columns)

    # Add "interest_id" to the new columns
    merge_cols = list(new_cols)  # Convert the set to a list
    merge_cols.append("unique_interest_id")  # Add "interest_id" to the list

    # Merge the dataframes
    merged_df = df.merge(
        data_w_extractable_amts[merge_cols], on="unique_interest_id", how="left"
    )
    return merged_df


# Stage 3: extract payer details and details about family members
def extract_third_party_details(df):
    """
    Takes dataframe and combines functions to extract details of family members and employers or third parties.
    Returns dataframe
    """

    # Extract details and progressively transform data
    data = extract_payer_details(df)
    data = extract_family_member_info(data)

    # Identify new columns in 'data' that aren't in 'df'
    new_cols = set(data.columns) - set(df.columns)

    # Add the merge column ("unique_interest_id") to ensure a common merge key
    merge_cols = list(new_cols)
    merge_cols.append("unique_interest_id")

    # Merge 'df' with 'data' using 'unique_interest_id' as the key, keeping 'df' as the left dataframe
    merged_df = df.merge(data[merge_cols], on="unique_interest_id", how="left")

    # extract details about employer and the role they provided to member of parliament
    merged_df = extract_mp_role_and_employer(merged_df)

    return merged_df


# stage 4: extract investments and assets
def extract_investments_and_assets(df):
    """
    Takes dataframe and combines functions that details about shareholding and property investments.
    Returns dataframe. TBC.
    """
    # TODO: write functions for this and incorporate into extraction pipeline.
    pass


# stage 4: save to database
def clean_and_save_to_database(df):
    """
    Takes dataframe and combines functions to clean the data and save it to the database.
    Returns the number of records saved to the database.
    """

    # TODO: rename df cols earlier/create them using database cols
    df_col_to_db_field_mapping = {
        "member_id": "member_of_parliament",
        "category_id": "category_id",
        "category_name": "category_name",
        "sort_order": "sort_order",
        "interest_id": "api_id",
        "unique_interest_id": "unique_api_generated_id",
        "interest": "interest_summary",
        "created_when": "date_created",
        "last_amended_when": "date_last_amended",
        "deleted_when": "date_deleted",
        "is_correction": "is_correction",
        "is_child_interest": "is_child_interest",
        "contains_time_periods_and_prepositions": "contains_time_period",
        "contains_debt_synonym": "contains_loan",
        "max_amount_currency": "interest_currency",
        "max_amount": "interest_amount",
        "donor_name": "payer",
        "donor_type": "payer_type",
        "donor_address": "payer_address",
        "companies_house_id": "payer_companies_house_id",
        "family_member_relationship": "family_member_relationship",
        "family_member_paid_by_mp_or_parliament": "family_member_paid_by_mp_or_parliament",
        "family_member_name": "family_member_name",
        "family_member_role": "family_member_role",
        "mp_role": "role",
        "parent_interest": "parent_interest",
        "employer_name": "employer_name",
    }

    # rename df cols to align with database field names
    df.rename(columns=df_col_to_db_field_mapping, inplace=True)

    # # create copy of df to operate on
    cols_for_db = [v for k, v in df_col_to_db_field_mapping.items()]
    df = df[cols_for_db].copy()

    # standardise the datetime formats in date cols
    date_columns = ["date_created", "date_last_amended", "date_deleted"]
    for col in date_columns:
        df[col] = df[col].apply(parse_and_format_dates)

    # Format datatypes and strings
    check_and_adjust_column_types(df, RegisteredInterest)
    df = truncate_strings_to_max_length(df)

    # save to db
    result = bulk_save_data(df)

    return result
