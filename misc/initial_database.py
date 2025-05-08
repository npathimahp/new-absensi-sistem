import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": "https://faceabsence-743dd-default-rtdb.firebaseio.com/",
    },
)
# menambahkan data dosen
ref = db.reference("Admins")

data = {
    "123456": {
        "id": "123456",
        "name": "Staff IT",
        "password": "admin",
        "email": "admin@gmail.com",
    },
}


for key, value in data.items():
    ref.child(key).set(value)
