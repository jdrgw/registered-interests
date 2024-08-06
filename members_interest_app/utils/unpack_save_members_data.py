# TODO: refactor to make generic and reusable

import os
import json
import logging
from datetime import datetime
from django.utils import timezone
from members_interest_app.models import MemberOfParliament 
from django.db import transaction


logger = logging.getLogger(__name__)

@transaction.atomic
def unpack_save_members_data():

    """
    Unpacks data about Members of Parliament pulled from Parliament API stored above django project directory.
    Creates a MemberOfParliament instance for each JSON object.
    Possibly one-time use as calling API should be handled within the django project itself.
    """
    
    total_added = 0
    total_updated = 0
    total_errors = 0

    current_dir = os.path.dirname(os.path.realpath(__file__))
    members_json_file = os.path.join(current_dir, "../../../call_members_api/members_of_parliament.json")

    # check whether JSON file exists
    try:
        with open(members_json_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError as fnfe:
        logger.error(f"File {members_json_file} not found.")
        total_errors+=1
        raise fnfe
    except json.JSONDecodeError as jde:
        logger.error(f"Error decoding JSON in file {members_json_file}.")
        total_errors+=1
        raise jde
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing JSON file: {e}")
        total_errors+=1
        raise e

    # Loop through JSON objects and save to or update to database 
    house_mapping = {
        1: "House of Commons",
        2: "House of Lords"
    }

    for obj in data:
        mps = obj.get("value")

        if mps:
            seat_data = mps.get("latestHouseMembership")
            try:
                # TODO: explore bulk update or save for effficient
                api_id = mps.get("id")

                # Get membership start and end dates, handling None values
                membership_start_str = seat_data.get("membershipStartDate")
                membership_end_str = seat_data.get("membershipEndDate")

                if membership_start_str is None:
                    membership_start_aware = None
                else:
                    membership_start_dt = datetime.strptime(membership_start_str, '%Y-%m-%dT%H:%M:%S')
                    membership_start_aware = timezone.make_aware(membership_start_dt, timezone.utc)

                if membership_end_str is None:
                    membership_end_aware = None
                else:
                    membership_end_dt = datetime.strptime(membership_end_str, '%Y-%m-%dT%H:%M:%S')
                    membership_end_aware = timezone.make_aware(membership_end_dt, timezone.utc)

                member, created = MemberOfParliament.objects.update_or_create(
                    api_id=api_id,
                    defaults={
                        "api_id": api_id,
                        "name": mps.get("nameDisplayAs"),
                        "gender": mps.get("gender", "Undisclosed"),
                        "thumbnail_url": mps.get("thumbnailUrl"),
                        "constituency": seat_data.get("membershipFrom", "Undisclosed"),
                        "membership_start": membership_start_aware,
                        "membership_end": membership_end_aware,
                        "membership_end_reason": seat_data.get("membershipEndReason", "Undisclosed"),
                        "membership_end_notes": seat_data.get("membershipEndReasonNotes", "Undisclosed"),
                        "house": house_mapping.get(seat_data.get("house"), "TBC")
                    }
                )
                if created:
                    total_added += 1
                else:
                    total_updated += 1
            except Exception as e:
                logger.error(f"Error processing member data: {e}. Member api_id is: {api_id}")
                total_errors += 1
    # log the counts of errors and , number members created, number members updated
    outcome = f'Total members added: {total_added}, Total members updated: {total_updated}, Total errors: {total_errors}'
    logger.info(outcome)
    return outcome


    