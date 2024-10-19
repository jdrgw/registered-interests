import os
import sys
import django
from django.conf import settings
import re
import requests
import json
from datetime import datetime
import time
import traceback


# MAKE FUNCTION CALLABLE WITHOUT MGMT COMMAND TEMPORARILY FOR PROTOTYPING

# Dynamically set the project root directory (relative to this script)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the project root to sys.path
sys.path.append(ROOT_DIR)

# Set the environment variable for Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parliament_data.settings')

# Initialize Django
django.setup()


# WRITE FUNCTION
from members_interest_app.models import MemberOfParliament

REGISTERED_INTEREST_API = "https://members-api.parliament.uk/api/Members/{}/RegisteredInterests"
ATTEMPTS = 2
INITIAL_WAIT = 5
BATCH_SIZE = 10


def extract_api_ids_from_file(file_path):
    try:
        file_api_ids = set()
        
        with open(file_path, "r") as file:
            read_file = file.read()

            json_objs = [obj for obj in read_file.split("\n\n\n") if obj.strip()]
            
            for obj in json_objs:
                data = json.loads(obj)
                links = data.get("links")
                
                if links and isinstance(links, list) and len(links) > 0:
                    extracted_api_id = links[0].get("href")
                else:
                    print(f"No valid 'links' array in object: {data}")
                    continue
                
                match = re.search(r'/Members/(\d+)/Interests', extracted_api_id)
                if match:
                    file_api_ids.add(match.group(1))
                else:
                    print(f"no match for {links} when searching for in-file api_ids")
                    continue

    except Exception as e:
            # Print the type of exception
            print(f"{type(e).__name__} occurred.")

            # Print the exception's args (the error message or relevant data)
            if hasattr(e, 'args'):
                print(f"args: {e.args}")
            
            # For AttributeError, print the attribute that caused the error
            if isinstance(e, AttributeError) and hasattr(e, 'name'):
                print(f"name: {e.name}")

            # Print the detailed traceback info (file name, line number, and code)
            tb = traceback.extract_tb(e.__traceback__)
            for frame in tb:
                print(f"File: {frame.filename}, Line: {frame.lineno}, in {frame.name}")
                print(f"  Code: {frame.line}")

    return file_api_ids

def call_api_and_save_data(file_path=None):

    if file_path is None:
        file_path = os.path.join(
        settings.BASE_DIR,
        "data",
        "registered_interest_data",
        "raw_data",
        f"registered_interests_{datetime.now().strftime('%Y-%m-%d')}.json"
        )
    else:
        file_path=file_path

    member_api_ids = (
        MemberOfParliament
        .objects
        .filter(api_id__isnull=False)
        .order_by("api_id")
        .values_list(
            'api_id', 
            flat=True
            )
        )

    # member_api_ids = ["1","2"]

    api_ids_from_file = extract_api_ids_from_file(file_path)
    failed_api_ids = []


    with requests.Session() as s:
        with open(file_path, "a") as file:
            for i in range(0, len(member_api_ids), BATCH_SIZE):
                batch = member_api_ids[i:i + BATCH_SIZE]

                for index in batch:
                    if index in api_ids_from_file:
                        print(f"Skipping already processed api_id: {index}")
                        continue

                    success = False
                    wait_time = INITIAL_WAIT

                    # Retry loop for each index (API ID)
                    for attempt in range(1, ATTEMPTS + 1):
                        try:
                            print(f"Attempting to fetch data for api_id: {index}, Attempt: {attempt}")
                            response = s.get(REGISTERED_INTEREST_API.format(index))

                            if response.status_code == 200:
                                registered_interest_ob = response.json()
                                json.dump(registered_interest_ob, file, indent=4)
                                file.write('\n\n\n')
                                success = True
                                break  # Exit retry loop on success
                            elif 500 <= response.status_code < 600:  # Server errors, retry
                                print(f"Server error ({response.status_code}) for api_id: {index}")
                            elif response.status_code == 429 and 'Retry-After' in response.headers:
                                wait_time = int(response.headers['Retry-After'])
                                print(f"Rate-limited for api_id: {index}, retrying after {wait_time} seconds...")
                            else:
                                # For non-retriable errors (like 404), no need to retry
                                print(f"Non-retriable error ({response.status_code}) for api_id: {index}")
                                break 

                        except requests.exceptions.RequestException as e:
                            print(f"Network error on attempt {attempt} for api_id {index}: {str(e)}")
                            traceback.print_exc()

                        if not success:
                            # Wait with exponential backoff
                            time.sleep(wait_time)
                            wait_time *= 2

                    if not success:
                        print(f"Failed to retrieve data for api_id: {index} after {ATTEMPTS} attempts")
                        failed_api_ids.append(index)

                time.sleep(INITIAL_WAIT)

    # Print or log any failed API IDs for later review
    if failed_api_ids:
        print(f"Failed to retrieve data for the following API IDs: {failed_api_ids}")
    
    # return api_ids_from_file, failed_api_ids


# call_api_and_save_data()