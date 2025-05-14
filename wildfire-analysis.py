import os
import time
import requests
import csv
import xml.etree.ElementTree as ET
from typing import List, Optional

# Constants for WildFire API and upload delay
WILDFIRE_API_URL = 'https://wildfire.paloaltonetworks.com/publicapi'
UPLOAD_DELAY = 1  # seconds

# Define variables for API key, directory, and CSV file name
api_key = "YOUR_WILDFIRE_API_KEY_HERE"  # Replace with your actual API key
directory_to_upload = "/path/to/your/files"  # Replace with the path to the directory containing files to upload
output_csv_file = "analysis_results.csv"  # Replace with the desired name for the output CSV file


def get_wildfire_verdict(api_key: str, sha256: str, max_attempts: int = 3, delay: int = 3) -> List[str]:
    """
    Retrieves the WildFire verdict for a given SHA256 hash with retry logic.

    Args:
        api_key: The WildFire API key.
        sha256: The SHA256 hash of the file to query.
        max_attempts: Maximum number of attempts to retrieve the verdict. Defaults to 3.
        delay: Delay in seconds between attempts. Defaults to 3.

    Returns:
        A list of verdicts or error messages from each attempt.
    """
    url = f'{WILDFIRE_API_URL}/get/verdict'
    data = {'apikey': api_key, 'hash': sha256}
    verdicts = []

    time.sleep(1)  # Add a 1-second delay before the first attempt

    for attempt in range(max_attempts):
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            xml_content = response.content
            root = ET.fromstring(xml_content)
            verdict_element = root.find('.//verdict')
            verdict = verdict_element.text if verdict_element is not None else 'Verdict Not Found'
            verdicts.append(verdict)
            print(f"Attempt {attempt + 1} verdict: {verdict}")
        except requests.exceptions.RequestException as e:
            print(f"Error getting verdict (attempt {attempt + 1}/{max_attempts}): {e}")
            verdicts.append(f"Error: {e}")
        except ET.ParseError as e:
            print(f"Error parsing XML (attempt {attempt + 1}/{max_attempts}): {e}")
            verdicts.append(f"Parse Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred (attempt {attempt + 1}/{max_attempts}): {e}")
            verdicts.append(f"Unexpected Error: {e}")

        if attempt < max_attempts - 1:
            time.sleep(delay)  # Delay before the next attempt

    return verdicts



def upload_file(api_key: str, file_path: str, csv_writer: csv.DictWriter) -> None:
    """
    Uploads a file to WildFire and retrieves the verdict, writing the results to a CSV file.

    Args:
        api_key: The WildFire API key.
        file_path: The path to the file to upload.
        csv_writer: The CSV writer object.
    """
    url = f'{WILDFIRE_API_URL}/submit/file'
    try:
        with open(file_path, 'rb') as file_to_upload:
            files = {'file': file_to_upload}
            data = {'apikey': api_key}
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()  # Raise HTTPError for bad responses
            xml_content = response.content
            root = ET.fromstring(xml_content)

            print(f"Successfully uploaded: {file_path} - Response: {xml_content}")

            # Extract file information from the XML response
            upload_file_info = root.find('upload-file-info')
            file_name = os.path.basename(file_path)
            file_type = upload_file_info.find('filetype').text if upload_file_info is not None and upload_file_info.find('filetype') is not None else ''
            sha256 = upload_file_info.find('sha256').text if upload_file_info is not None and upload_file_info.find('sha256') is not None else ''
            md5 = upload_file_info.find('md5').text if upload_file_info is not None and upload_file_info.find('md5') is not None else ''
            file_size_bytes = upload_file_info.find('size').text if upload_file_info is not None and upload_file_info.find('size') is not None else '0'
            file_size_mb = float(file_size_bytes) / (1024 * 1024)
            file_size_mb_str = f"{file_size_mb:.2f} MB"

            # Get WildFire verdict
            verdicts = get_wildfire_verdict(api_key, sha256)
            verdicts = verdicts + [''] * (3 - len(verdicts))  # Pad verdicts list

            # Write data to CSV
            csv_writer.writerow({
                'FileName': file_name,
                'FileType': file_type,
                'SHA256': sha256,
                'MD5': md5,
                'FileSize': file_size_mb_str,
                'Verdict (+1s)': verdicts[0],
                'Verdict 2 (+3s)': verdicts[1],
                'Verdict 3 (+3s)': verdicts[2],
            })

    except requests.exceptions.RequestException as e:
        print(f"Failed to upload {file_path}. Error: {e}")
    except ET.ParseError as e:
        print(f"Failed to parse XML response for {file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        time.sleep(UPLOAD_DELAY)



def upload_files_in_directory(directory: str, api_key: str, csv_file_path: str) -> None:
    """
    Uploads all files in a directory to WildFire and saves results to a CSV file.

    Args:
        directory: The path to the directory containing files to upload.
        api_key: The WildFire API key.
        csv_file_path: The path to the CSV file to write results to.
    """
    if not os.path.isdir(directory):
        print(f"Error: The directory '{directory}' does not exist.")
        return

    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['FileName', 'FileType', 'SHA256', 'MD5', 'FileSize', 'Verdict (+1s)', 'Verdict 2 (+3s)', 'Verdict 3 (+3s)']
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csv_writer.writeheader()

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                upload_file(api_key, file_path, csv_writer)
            else:
                print(f"Skipping '{file_path}', as it is not a file.")



if __name__ == "__main__":
    # Use the variables defined at the beginning of the script
    # api_key = input("Enter your WildFire API key: ") # Removed input
    # directory_to_upload = input("Enter the directory containing files to upload: ") # Removed input
    # output_csv_file = input("Enter the name of the output CSV file (e.g., wildfire_results.csv): ") # Removed input

    # Check for empty input
    if not api_key:
        print("Error: API key is required.")
        exit()
    if not os.path.isdir(directory_to_upload):
        print(f"Error: Directory '{directory_to_upload}' does not exist.")
        exit()
    if not output_csv_file:
        print("Error: Output CSV file name is required.")
        exit()

    upload_files_in_directory(directory_to_upload, api_key, output_csv_file)
    print(f"\nAnalysis results saved to: {output_csv_file}")
