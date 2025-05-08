import os
import json
import base64

# Cache for encoded faces
ENCODE_FILE = "EncodeFile.p"  # Path to the encoded faces file

# Secret key for Flask session
SECRET_KEY = os.environ.get("SECRET_KEY", "default-key")  # Change this to a random string

FIREBASE_CREDENTIALS = json.loads(
    base64.b64decode(os.getenv("FIREBASE_CREDENTIALS_BASE64")).decode("utf-8")
)

DATABASE_URL = os.getenv("DATABASE_URL")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")
SECRET_KEY = os.getenv("SECRET_KEY", "default-key")

