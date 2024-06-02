import os
import json
import logging
from django.core.exceptions import ValidationError
from .models import MemberOfParliament  
import logging
from datetime import datetime

# TODO: refactor to make generic and reusable

logger = logging.getLogger(__name__)

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
    members_json_file = os.path.join(current_dir, "../../call_members_api/members_of_parliament.json")

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
                member, created = MemberOfParliament.objects.update_or_create(
                    api_id=mps.get("id"),
                    defaults={
                        "name": mps.get("nameDisplayAs"),
                        "gender": mps.get("gender", "Undisclosed"),
                        "thumbnail_url": mps.get("thumbnailUrl"),
                        "constituency": seat_data.get("membershipFrom", "Undisclosed"),
                        "membership_start": seat_data.get("membershipStartDate"),
                        "membership_end": seat_data.get("membershipEndDate"),
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
                logger.error(f"Error processing member data: {e}")
                total_errors += 1
    # log the counts of errors and , number members created, number members updated
    logger.info(f'Total members added: {total_added}, Total members updated: {total_updated}, Total errors: {total_errors}')