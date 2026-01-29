import os
import subprocess
import sys
import time
import json
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
                print("API response successful")
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
        print("Cannot connect to API server.")
    except requests.exceptions.Timeout:
        print("API request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
    except json.JSONDecodeError:
        print("Invalid JSON response from API.")
    
    # Return default values if API fails
    print("Using default values...")
    return {
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

def get_final_filename(output_file, version):
    """Generate final filename: output_file + version + .exe"""
    if not version:
        return f"{output_file}.exe"
    
    # Remove .exe if present in output_file
    if output_file.lower().endswith('.exe'):
        base_name = output_file[:-4]
    else:
        base_name = output_file
    
    # Create filename: base_name + _ + version + .exe
    return f"{base_name}_{version}.exe"

def check_file_exists(output_file, version):
    """Check if the specific version file already exists"""
    target_filename = get_final_filename(output_file, version)
    
    if os.path.exists(target_filename):
        print(f"File already exists: {target_filename}")
        file_size = os.path.getsize(target_filename)
        print(f"File size: {file_size:,} bytes")
        return target_filename
    
    # Also check for the base filename without version
    if version:
        base_filename = f"{output_file}.exe"
        if os.path.exists(base_filename):
            print(f"Found base file (without version): {base_filename}")
            # Rename it to include version
            final_filename = get_final_filename(output_file, version)
            try:
                os.rename(base_filename, final_filename)
                print(f"Renamed to: {final_filename}")
                return final_filename
            except Exception as e:
                print(f"Error renaming file: {e}")
                return base_filename
    
    return None

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

def main():
    target_path = "C:/Documents/ChatUgautodetal"
    
    # Create and change directory
    os.makedirs(target_path, exist_ok=True)
    os.chdir(target_path)
    print(f"Working in: {os.getcwd()}")
    
    # Step 1: Get version info from API
    api_info = get_version_from_api()
    
    if not api_info["data"]:
        print("No API data received. Please check your connection.")
        return
    
    file_id = api_info["data"].get("file_id", "")
    output_file = api_info["data"].get("output_file", "")
    current_version = api_info["data"].get("version", "")
    api_data = api_info["data"]
    
    print(f"\nAPI Info received:")
    print(f"  Output File: {output_file}")
    print(f"  Current Version: {current_version}")
    print(f"  File ID: {file_id}")
    
    if not output_file:
        print("Error: No output file specified in API response")
        return
    
    # Step 2: Check if we already have this exact version
    final_filename = get_final_filename(output_file, current_version)
    print(f"\nTarget filename: {final_filename}")
    
    existing_file = check_file_exists(output_file, current_version)
    
    if existing_file:
        print(f"\nFound existing file: {existing_file}")
        
        # Check if it's the exact version we need
        if existing_file == final_filename:
            print("Exact version match found!")
            start_application(existing_file, api_data)
        else:
            print(f"Different version found. Will check for updates...")
    
    # Step 3: Download new version if needed
    print(f"\nChecking for updates...")
    
    if existing_file and not current_version:
        # No version info from API, just run existing file
        print("No version info from API. Running existing file...")
        start_application(existing_file, api_data)
        return
    
    # Step 4: Download new version
    if not file_id:
        print("Error: No file ID specified in API response")
        if existing_file:
            print("Starting existing file...")
            start_application(existing_file, api_data)
        return
    
    print(f"\nDownloading new version...")
    
    # Create temporary filename for download
    temp_filename = f"{output_file}"
    
    download_success = False
    
    # Method 1: Try curl first
    print("\nAttempting download with curl...")
    try:
        direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        subprocess.run(["curl", "-L", "-o", temp_filename, direct_url], 
                      check=True, capture_output=True, text=True)
        download_success = os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0
    except Exception as e:
        print(f"Curl failed: {e}")
        download_success = False
    
    # Method 2: Try gdown if curl failed
    if not download_success:
        print("Curl failed, trying gdown...")
        try:
            download_success = download_with_gdown(file_id, temp_filename)
        except Exception as e:
            print(f"Gdown failed: {e}")
            download_success = False
    
    # Method 3: Try wget as last resort
    if not download_success:
        print("Trying wget...")
        try:
            direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            subprocess.run(["wget", "-O", temp_filename, direct_url], 
                          check=True, capture_output=True, text=True)
            download_success = os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0
        except Exception as e:
            print(f"Wget failed: {e}")
            download_success = False
    
    if download_success:
        print(f"\nDownload successful: {temp_filename}")
        file_size = os.path.getsize(temp_filename)
        print(f"File size: {file_size:,} bytes")
        
        # Rename to final filename with version
        try:
            os.rename(temp_filename, final_filename)
            print(f"Renamed to: {final_filename}")
        except Exception as e:
            print(f"Error renaming file: {e}")
            final_filename = temp_filename
        
        # Save API data to a JSON file alongside the executable
        if api_data:
            data_filename = final_filename.replace('.exe', '_data.json')
            try:
                with open(data_filename, 'w') as f:
                    json.dump(api_data, f, indent=2)
                print(f"Saved API data to: {data_filename}")
            except Exception as e:
                print(f"Error saving API data: {e}")
        
        # Start the application
        print("\nStarting application with API data...")
        start_application(final_filename, api_data)
        
    else:
        print("\nAll download methods failed.")
        
        # Try to start existing file if download fails
        if existing_file:
            print(f"Attempting to start existing file: {existing_file}")
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