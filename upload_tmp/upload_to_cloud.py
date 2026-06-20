import os
import zipfile
import requests
import sys

def create_zip():
    zip_filename = "video_factory.zip"
    files_to_zip = ["main.py", "app.py", "config.json", "setup_cloud.sh", "requirements.txt"]
    dirs_to_zip = ["core", "assets"]
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in files_to_zip:
            if os.path.exists(f):
                zipf.write(f)
        for d in dirs_to_zip:
            if os.path.exists(d):
                for root, _, files in os.walk(d):
                    if '__pycache__' in root:
                        continue
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path)
    return zip_filename

def upload_file(filename):
    print("Uploading to file.io...")
    with open(filename, 'rb') as f:
        response = requests.post('https://file.io', files={'file': f})
        if response.status_code == 200:
            link = response.json().get('link')
            print(f"UPLOAD_SUCCESS: {link}")
        else:
            print(f"UPLOAD_FAILED: {response.text}")

if __name__ == "__main__":
    z = create_zip()
    upload_file(z)
