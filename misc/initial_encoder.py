import os

import cv2
import pickle
import face_recognition
import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(
    cred,
    {
        "databaseURL": "https://faceabsence-743dd-default-rtdb.firebaseio.com/",
        "storageBucket": "faceabsence-743dd.appspot.com",
    },
)

# Memuat Gambar Mahasiswa
folderPath = "./app/static/Files/Images"
imgPathList = os.listdir(folderPath)
print(imgPathList)
imgList = []
studentIDs = []

for path in imgPathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    studentIDs.append(os.path.splitext(path)[0])
    # Mengunggah Gambar ke Firebase
    fileName = f"{folderPath}/{path}"
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)

print(studentIDs)


def find_encodings(images):
    """Find the encodings of the images."""
    encodeList = []

    for img in images:
        # mengonversi gambar dari BGR ke RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList


print("Encoding Started")

# Membuat Encoding
encodeListKnown = find_encodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentIDs]

file = open("EncodeFile.p", "wb")
pickle.dump(encodeListKnownWithIds, file)  # Menyimpan Encoding
file.close()

print("Encoding Ended")
