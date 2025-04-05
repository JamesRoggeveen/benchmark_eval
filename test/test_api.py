import requests
import json
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

def test_latex_render():
    # Load test data
    with open('test/test_data/test_render.json', 'r') as f:
        data = json.load(f)
    
    # Print current storage mode
    print(f"Testing with storage mode: {'local' if os.environ.get('USE_LOCAL_STORAGE', 'false').lower() == 'true' else 'cloud'}")
    
    # Send request to local server
    response = requests.post(
        'http://localhost:8080/render',
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    # Parse the response
    response_data = response.json()
    
    # Check if request was successful
    if response.status_code == 200:
        file_url = response_data['file_url']
        print(f"Success! File available at: {file_url}")
        
        # Verify URL has proper scheme
        parsed_url = urlparse(file_url)
        if not parsed_url.scheme:
            print(f"Warning: URL {file_url} is missing scheme, attempting to add http://")
            file_url = f"http://localhost:8080{file_url}"
        
        # Optionally download the file
        download_response = requests.get(file_url)
        if download_response.status_code == 200:
            with open('output/downloaded_test.pdf', 'wb') as f:
                f.write(download_response.content)
            print(f"Successfully downloaded file to: output/downloaded_test.pdf")
        else:
            print(f"Warning: Could not download file from {file_url}")
            print(f"Status code: {download_response.status_code}")
            print(f"Response: {download_response.text}")
    else:
        print(f"Error: {response_data.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_latex_render() 