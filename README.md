# WildFire API Script

## Description

This Python script automates the process of submitting files to the Palo Alto Networks WildFire API for analysis and retrieving the analysis results. It performs the following actions:

* Uploads files from a specified directory to the WildFire API.
* Retrieves the WildFire verdict for each uploaded file, with multiple attempts (3) to ensure accuracy.
* Saves the file information and verdict to a CSV file
  
## Features

* File upload to WildFire API.
* Verdict retrieval with retry logic (3 attempts with a 3-second delay).
* Data extraction from WildFire API XML responses.
* CSV output of file information and verdicts.
* Error handling for network requests and XML parsing.
* File size formatting in megabytes.

## Requirements

* Python 3.x
* Requests library (`pip install requests`)
* A Palo Alto Networks WildFire API key.

## Setup

1.  **Install Python**: Ensure you have Python 3.x installed on your system.
2.  **Install the Requests library**:
    ```bash
    pip install requests
    ```
3.  **Obtain a WildFire API key**: You need a valid API key from Palo Alto Networks to use the WildFire API.
4.  **Clone the repository**: Clone this GitHub repository to your local machine.
5.  **Configure the script**:
    * Open the `wildfire_upload.py` script.
    * Modify the following variables at the beginning of the script:
        * `api_key`: Replace `"YOUR_API_KEY"` with your actual WildFire API key.
        * `directory_to_upload`: Replace `"/path/to/your/files"` with the path to the directory containing the files you want to upload.
        * `output_csv_file`: Replace `"wildfire_analysis_results.csv"` with the desired name for the output CSV file.

## Usage

1.  **Place files in the upload directory**: Put the files you want to analyze into the directory specified by the `directory_to_upload` variable in the script.
2.  **Run the script**: Open your terminal or command prompt, navigate to the directory where you saved the script, and run it using:
    ```bash
    python wildfire_upload.py
    ```
3.  **Check the output**: The script will upload the files, retrieve the verdicts, and save the results in a CSV file named as specified in the `output_csv_file` variable.

## CSV Output

The script creates a CSV file with the following columns:

* `FileName`: The name of the uploaded file.
* `FileType`: The type of the uploaded file.
* `SHA256`: The SHA256 hash of the uploaded file.
* `MD5`: The MD5 hash of the uploaded file.
* `FileSize`: The size of the uploaded file in megabytes (MB).
* `Verdict (+1s)`: The verdict from the first attempt (with a 1-second delay).
* `Verdict 2 (+3s)`: The verdict from the second attempt (with a 3-second delay).
* `Verdict 3 (+3s)`: The verdict from the third attempt (with a 3-second delay).

## Error Handling

The script includes error handling for the following:

* Invalid directory path.
* Failed file uploads.
* XML parsing errors.
* Network errors during verdict retrieval.
* General exceptions.

## Rate Limiting

The script includes a delay of 1 second before the first verdict attempt and 3 seconds between subsequent attempts to comply with potential API rate limits. The `UPLOAD_DELAY` variable (currently set to 1 second) introduces a delay between file uploads. Adjust these values as needed based on the WildFire API rate limit policy.

## Disclaimer

This script is provided as-is. Use it at your own risk. Ensure you comply with the Palo Alto Networks WildFire API terms of service.
