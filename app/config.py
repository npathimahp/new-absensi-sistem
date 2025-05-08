import os
import json
from dotenv import load_dotenv

# Cache for encoded faces
ENCODE_FILE = "EncodeFile.p"  # Path to the encoded faces file

# Secret key for Flask session
SECRET_KEY = os.environ.get("SECRET_KEY", "default-key")  # Change this to a random string

# Firebase configuration details
load_dotenv()

import os

FIREBASE_CREDENTIALS = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),  # pastikan newline dipulihkan
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
}

DATABASE_URL = os.getenv("DATABASE_URL")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")
SECRET_KEY = os.getenv("SECRET_KEY", "default-key")

