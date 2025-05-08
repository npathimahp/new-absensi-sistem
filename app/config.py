import os
import json
from dotenv import load_dotenv

# Cache for encoded faces
ENCODE_FILE = "EncodeFile.p"  # Path to the encoded faces file

# Secret key for Flask session
SECRET_KEY = os.environ.get("SECRET_KEY", "default-key")  # Change this to a random string

# Firebase configuration details
load_dotenv()

FIREBASE_CREDENTIALS = json.loads(os.environ.get("FIREBASE_CREDENTIALS"))
DATABASE_URL = os.environ.get("DATABASE_URL")
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET")
