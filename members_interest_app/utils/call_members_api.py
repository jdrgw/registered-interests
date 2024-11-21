import json
import logging
import os
import time
from datetime import datetime

import requests
from django.conf import settings

ATTEMPTS = 3
INITIAL_WAIT = 5
BATCH_SIZE = 10
BAD_STATUSES = [429, 500, 502, 503, 504]
TERMINATION_THRESHOLD = 250


def append_to_json_file(data, title):
    """
    Append data to a JSON file.

    Args:
        data: The data to be appended.
        title: The filename of the JSON file.
    """
    # print(data) # for debugging
    try:
        with open(title, "r") as infile:
            existing_data = json.load(infile)
    except FileNotFoundError:
        existing_data = []
        existing_data.append(data)

    # Ensure no duplicates
    if data not in existing_data:
        existing_data.append(data)

    with open(title, "w") as outfile:
        json.dump(existing_data, outfile, indent=4)

    # # Debug statement - retain for later debugging.
    # print(f"Data written to {title}: {existing_data}")


def test_json_validity(response, index):
    """
    Test the validity of JSON data extracted from an HTTP response.

    Args:
        response: The HTTP response object.
        index: The index associated with the response.

    Returns:
        A dictionary containing information about the response, including any errors encountered.
    """
    status_code = response.status_code
    try:
        content = response.json()
        content["status_code"] = status_code
        content["searched_index"] = index

    except ValueError:
        content = {
            "content": response.content.decode("utf-8"),
            "status_code": status_code,
            "searched_index": index,
        }
    return content


def fetch_members_data():
    n = list(range(1, 6000))
    url = "https://members-api.parliament.uk/api/Members"
    data = {}
    status_log = []
    termination_condition = False

    today_date = datetime.now().strftime("%Y-%m-%d")

    # Paths to save files with date
    json_file_path = os.path.join(
        settings.BASE_DIR,
        "data",
        "members_data",
        "raw_data",
        f"members_of_parliament_{today_date}.json",
    )

    # Ensure the directory exists
    os.makedirs(os.path.dirname(json_file_path), exist_ok=True)

    session = requests.Session()

    print(f"Fetching data and saving to {json_file_path}")

    for i in range(0, len(n), BATCH_SIZE):
        batch = n[i : i + BATCH_SIZE]  # create batch

        for index in batch:
            if index % 200 == 0:
                print(f"Processed {index} indexes...")

            attempt = 0
            inner_wait = INITIAL_WAIT

            # try getting responses up to # ATTEMPTS with exponential back off and dynamic pausing
            while attempt < ATTEMPTS:
                attempt += 1

                try:
                    start_time = time.time()
                    response = session.get(f"{url}/{index}")
                    end_time = time.time()
                    response_time = end_time - start_time
                except requests.RequestException as e:
                    # Handle network errors
                    logging.error(f"Network error occurred: {e}")
                    continue
                except json.JSONDecodeError as e:
                    # Handle JSON parsing errors
                    logging.error(f"Error parsing JSON response: {e}")
                    continue
                except Exception as e:
                    # Handle other unexpected errors
                    logging.error(f"An unexpected error occurred: {e}")
                    continue

                data[index] = response
                content = test_json_validity(data[index], index)

                append_to_json_file(data=content, title=json_file_path)

                status_code = response.status_code
                status_log.append(status_code)
                # creating logging entry for debugging
                logging.info(
                    f"Index: {index}, Status Code: {status_code}, Response Time: {response_time} seconds, Response Headers: {response.headers}"
                )

                # handle bad statuses by implementing server recommended wait time or exponential backoff
                if status_code in BAD_STATUSES:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        wait_time = int(retry_after) + 2
                        time.sleep(wait_time)
                    else:
                        inner_wait *= 2
                        time.sleep(inner_wait)
                else:
                    break

            # break out of loop if last TERMINATION_THRESHOLD statuses are bad and set termination flag to break out of outer loop too
            if (
                len(status_log) >= TERMINATION_THRESHOLD
                and (
                    all(
                        element in BAD_STATUSES
                        for element in status_log[-TERMINATION_THRESHOLD:]
                    )
                    # 404 is bad status but treated separately as lots of ids 404 and i aim to reduce # attempts
                    or all(
                        element == 404
                        for element in status_log[-TERMINATION_THRESHOLD:]
                    )
                )
            ):
                termination_condition = True
                break

        # delay between each batch
        time.sleep(INITIAL_WAIT)

        if termination_condition:
            break

    session.close()
    print(f"Finished fetching data and saved to {json_file_path}")
