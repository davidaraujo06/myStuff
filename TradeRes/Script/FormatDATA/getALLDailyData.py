import os
import requests
import re  # Module for regular expression operations

# Directory where CSV files will be saved
save_dir = './csv_files_2023'  # Replace with desired path

# Ensure the save directory exists, create if it doesn't
os.makedirs(save_dir, exist_ok=True)

# Base URL for downloading files
base_url = 'https://www.omie.es/pt/file-download?parents%5B0%5D=marginalpdbcpt&filename=marginalpdbcpt_'

# Function to download a file from a URL
def download_csv(url, save_dir):
    # Use regular expression to replace invalid characters in the URL
    file_name = re.sub(r'[\\/:*?"<>|]', '_', url.split('=')[-1])

    os.makedirs(save_dir, exist_ok=True)

    # Make HTTP request to get the file content
    response = requests.get(url)

    # Check if request was successful (status code 200)
    if response.status_code == 200:
        # Open file in binary mode and write the downloaded content
        with open(os.path.join(save_dir, file_name), 'wb') as f:
            f.write(response.content)
        print(f'File {file_name} downloaded and saved successfully.')
    else:
        print(f'Failed to download file {file_name}. Response status: {response.status_code}')

# Iterate over months (from 1 to 12)
for month in range(1, 13):
    # Iterate over days of the month (from 1 to 31)
    # Use a range based on the maximum number of days possible in a month to avoid downloading files for non-existent days
    for day in range(1, 32):
        try:
            # Build date string in YYYYMMDD format
            date_str = f'2023{month:02d}{day:02d}'
            
            # Build URL for the current day's CSV file
            url = f'{base_url}{date_str}.1'
            
            # Call the function to download and save the CSV file
            download_csv(url, save_dir)
        
        except Exception as e:
            print(f'Error processing day {day} of month {month}: {str(e)}')
