import os
import subprocess
import sys
import time
import json
from datetime import datetime
import requests

def get_version_from_api():
    """Get current version, file_id and output_file from local API"""
    api_url = "https://ugauto-back-version.vercel.app/version"
    
    try:
        print(f"Checking version from API: {api_url}")
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                print("API response successful", data)
                return {
                    "file_id": data.get("file_id", ""),
                    "output_file": data.get("output_file", ""),
                    "data": data.get("data", {})
                }
            else:
                print(f"API returned non-success status: {data.get('status')}")
        else:
            print(f"API request failed with status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Cannot connect to localhost:3000. Make sure the API server is running.")
    except requests.exceptions.Timeout:
        print("API request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
    except json.JSONDecodeError:
        print("Invalid JSON response from API.")
    
    # Return default values if API fails
    print("Using default values...")
    return {
        "current_version": "",
        "file_id": "",
        "output_file": "",
        "data": {}
    }

def download_with_gdown(file_id, output_file):
    """Alternative download method using gdown for Google Drive files"""
    try:
        import gdown
    except ImportError:
        print("Installing gdown package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
        import gdown
    
    url = f"https://drive.google.com/uc?id={file_id}"
    gdown.download(url, output_file, quiet=False)
    return os.path.exists(output_file)

def rename_with_version(original_file, api_version=None):
    """Rename file with version number"""
    if not os.path.exists(original_file):
        return original_file
    
    # Check if original file already has the base name pattern
    original_name = os.path.basename(original_file)
    
    # Determine version to use
    if api_version and api_version.strip():
        # Use version from API
        version = api_version
        print(f"Using API version: {version}")
    
    # Create new filename with version
    new_filename = f"{original_file}_{api_version}{'.ext'}"
    
    # Skip if same name
    if original_name == new_filename:
        print(f"File already has correct name: {original_name}")
        return original_file
    
    # Rename the file
    try:
        os.rename(original_file, new_filename)
        print(f"Renamed '{original_file}' to '{new_filename}'")
        return new_filename
    except Exception as e:
        print(f"Error renaming file: {e}")
        return original_file

def start_application(filename, api_data=None):
    """Start the application with optional API data"""
    print(f"\nStarting {filename}...")
    
    # Prepare environment with API data if available
    env = os.environ.copy()
    if api_data:
        # Pass API data as environment variables
        env['API_DATA'] = json.dumps(api_data)
        print(f"Passing API data to application")
    
    try:
        # Start the application with environment variables
        process = subprocess.Popen([filename], shell=True, env=env)
        print(f"Application started successfully! (PID: {process.pid})")
        
        # Wait a moment
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Error starting application: {e}")
        print(f"Try running it manually from: {os.path.abspath(filename)}")
        return False

def check_and_update_existing(base_name, api_version=None):
    """Check if existing file matches API version and update if needed"""
    existing_files = [f for f in os.listdir('.') if f.startswith(base_name) and f.endswith('.exe')]
    
    if not existing_files:
        return None
    
    print(f"Found existing application file(s): {existing_files}")
    
    if api_version:
        # Look for file with exact API version
        expected_name = f"{base_name}_{api_version}.exe"
        if expected_name in existing_files:
            print(f"Found exact version match: {expected_name}")
            return expected_name
        
        # Check if any existing file starts with the same version prefix
        for file in existing_files:
            # Extract version from filename (remove base_name_ and .exe)
            file_version = file.replace(f"{base_name}_", "").replace(".exe", "")
            if file_version.startswith(api_version.split('_')[0]):  # Compare date part
                print(f"Found similar version: {file}")
                return file
    
    # Return most recent file
    existing_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    latest_file = existing_files[0]
    print(f"Using most recent file: {latest_file}")
    
    return latest_file

def main():
    target_path = "C:/Documents/ChatUgautodetal"
    
    # Create and change directory
    os.makedirs(target_path, exist_ok=True)
    os.chdir(target_path)
    print(f"Working in: {os.getcwd()}")
    
    # Step 1: Get version info from API
    api_info = get_version_from_api()
    print(api_info)
    current_version = api_info["data"]['version']
    file_id = api_info["data"]["file_id"]
    output_file = api_info["data"]["output_file"]
    api_data = api_info["data"]
    
    print(f"\nAPI Info received:")
    print(f"  Current Version: {current_version}")
    print(f"  File ID: {file_id}")
    print(f"  Output File: {output_file}")
    print(f"  Data: {api_data}")
    
    # Base name for the renamed file
    base_name = "chatUgautodetal"
    
    # Step 2: Check if we already have this version
    existing_file = check_and_update_existing(base_name, current_version)
    
    if existing_file and current_version:
        # We have a version that matches (or is close to) the API version
        user_input = input(f"\nFound existing version. Do you want to run it? (yes/no): ").strip().lower()
        
        if user_input in ['yes', 'y', '']:
            start_application(existing_file, api_data)
            return
        else:
            print("Continuing with update...")
    
    # Step 3: Download new version
    print(f"\nDownloading new version from API info...")
    
    download_success = False
    
    # Method 1: Try curl first
    print("\nAttempting download with curl...")
    try:
        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        subprocess.run(["curl", "-L", "-o", output_file, direct_url], 
                      check=True, capture_output=True, text=True)
        download_success = os.path.exists(output_file) and os.path.getsize(output_file) > 0
    except Exception as e:
        print(f"Curl failed: {e}")
        download_success = False
    
    # Method 2: Try gdown if curl failed
    if not download_success:
        print("Curl failed, trying gdown...")
        try:
            download_success = download_with_gdown(file_id, output_file)
        except Exception as e:
            print(f"Gdown failed: {e}")
            download_success = False
    
    # Method 3: Try wget as last resort
    if not download_success:
        print("Trying wget...")
        try:
            direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            subprocess.run(["wget", "-O", output_file, direct_url], 
                          check=True, capture_output=True, text=True)
            download_success = os.path.exists(output_file) and os.path.getsize(output_file) > 0
        except Exception as e:
            print(f"Wget failed: {e}")
            download_success = False
    
    if download_success:
        print(f"\nDownload successful: {output_file}")
        file_size = os.path.getsize(output_file)
        print(f"File size: {file_size:,} bytes")
        
        # Rename with API version
        final_filename = rename_with_version(output_file, current_version)
        
        print(f"\nFinal file: {final_filename}")
        
        # Save API data to a JSON file alongside the executable
        if api_data:
            data_filename = final_filename.replace('.exe', '_data.json')
            with open(data_filename, 'w') as f:
                json.dump(api_data, f, indent=2)
            print(f"Saved API data to: {data_filename}")
        
        # Start the application
        print("\nStarting application with API data...")
        start_application(final_filename, api_data)
        
    else:
        print("\nAll download methods failed.")
        
        # Try to start existing file if download fails
        if existing_file:
            print(f"Attempting to start existing file: {existing_file}")
            user_input = input("Start existing version? (yes/no): ").strip().lower()
            if user_input in ['yes', 'y', '']:
                start_application(existing_file, api_data)
        else:
            print("Please check your connection and try again.")

if __name__ == "__main__":
    # Install requests if not available
    try:
        import requests
    except ImportError:
        print("Installing requests package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    main()