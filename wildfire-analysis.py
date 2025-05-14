import os
import time
import requests
import csv
import xml.etree.ElementTree as ET

UPLOAD_DELAY = 1  # seconds
WILDFIRE_API_URL = 'https://wildfire.paloaltonetworks.com/publicapi'  # Base URL

# Define variables for API key, directory, and CSV file name
api_key = "YOUR_WILDFIRE_API_KEY_HERE"  # Replace with your actual API key
directory_to_upload = "/path/to/your/files"  # Replace with the path to the directory containing files to upload
output_csv_file = "analysis_results.csv"  # Replace with the desired name for the output CSV file


def get_wildfire_verdict(api_key, sha256, max_attempts=3, delay=3):
    """Gets the WildFire verdict for a given SHA256 hash with retry logic."""
    url = f'{WILDFIRE_API_URL}/get/verdict'
    data = {'apikey': api_key, 'hash': sha256}  # Using SHA256 to get the verdict
    verdicts = []  # Store verdicts from each attempt
    time.sleep(1) # Add 1 second delay before the first attempt
    for attempt in range(max_attempts):
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            xml_content = response.content  # Get XML content
            root = ET.fromstring(xml_content)  # Parse XML
            verdict_element = root.find('.//verdict')  # Look for the verdict element
            verdict = verdict_element.text if verdict_element is not None else 'Verdict Not Found'
            verdicts.append(verdict)
            print(f"Attempt {attempt + 1} verdict: {verdict}")  # Print the verdict
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
            time.sleep(delay)  # Delay before next attempt
    return verdicts  # Return the list of verdicts/errors



def upload_file(api_key, file_path, csv_writer):
    """Uploads a file to WildFire and gets the verdict."""
    url = f'{WILDFIRE_API_URL}/submit/file'
    try:
        with open(file_path, 'rb') as file_to_upload:  # Use a context manager to ensure the file is closed.
            files = {'file': file_to_upload}
            data = {'apikey': api_key}
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()  # Raise an error for bad responses
            xml_content = response.content  # Get XML content
            root = ET.fromstring(xml_content)  # Parse XML
            print(f"Successfully uploaded: {file_path} - Response: {xml_content}")
            # Extract relevant data from the XML response
            file_name = os.path.basename(file_path)
            upload_file_info = root.find('upload-file-info')
            file_type = upload_file_info.find('filetype').text if upload_file_info.find('filetype') is not None else ''
            sha256 = upload_file_info.find('sha256').text if upload_file_info.find('sha256') is not None else ''
            md5 = upload_file_info.find('md5').text if upload_file_info.find('md5') is not None else ''
            file_size_bytes = upload_file_info.find('size').text if upload_file_info.find('size') is not None else '0'
            file_size_mb = float(file_size_bytes) / (1024 * 1024)  # Convert to MB
            file_size_mb_str = f"{file_size_mb:.2f} MB" # Format the file size
            # Get WildFire verdict
            verdicts = get_wildfire_verdict(api_key, sha256)  # Get verdict attempts
            # Pad the verdicts list to ensure it always has 3 elements
            verdicts = verdicts + [''] * (3 - len(verdicts))
            # Write data to CSV
            csv_writer.writerow([file_name, file_type, sha256, md5, file_size_mb_str, verdicts[0], verdicts[1], verdicts[2]])  # Write all verdicts
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload {file_path}. Error: {e}")
    except ET.ParseError as e:
        print(f"Failed to parse XML response for {file_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        time.sleep(UPLOAD_DELAY)  # Wait 30 seconds between uploads  (Corrected typo)


def upload_files_in_directory(directory, api_key, csv_file):
    """Uploads all files in a directory to WildFire and saves results to a CSV."""
    # Check if the directory exists
    if not os.path.isdir(directory):
        print(f"Error: The directory '{directory}' does not exist.")
        return
    # Open CSV file for writing
    with open(csv_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write header row
        csv_writer.writerow(
            ['FileName', 'FileType', 'SHA256', 'MD5', 'FileSize', 'Verdict (+1s)', 'Verdict 2 (+3s)', 'Verdict 3 (+3s)'])  # Adjusted header
        # Loop through each file in the directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            # Check if it's a file (not a directory)
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
