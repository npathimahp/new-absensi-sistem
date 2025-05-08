from datetime import datetime
import os
import pickle

from firebase_admin import db
import cv2
import numpy as np
import face_recognition
import cvzone

from .database import get_student_data
from .utils import (
    has_already_marked_attendance,
    mark_attendance,
    count_subject_attendance,
)
from . import config


def generate_frame(selected_subject):
    # Inisialisasi Kamera Menggunakan OpenCV
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # Membaca Background image menggunakan OpenCV
    imgBackground = cv2.imread("./app/static/Files/Resources/background.png")
    folderModePath = "./app/static/Files/Resources/Modes/"
    modePathList = os.listdir(folderModePath)
    imgModeList = []

    for path in modePathList:
        imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

    modeType = 0
    id = -1
    imgStudent = []
    counter = 0

    # memuat data wajah yang dikenali
    file = open(config.ENCODE_FILE, "rb")
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodedFaceKnown, studentIDs = encodeListKnownWithIds
    # pengolahan frame kamera
    while True:
        success, img = capture.read()

        if not success:
            break
        else:
            imgSmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)
            # Ini memanggil HOG detector dari dlib
            # Deteksi wajah menggunakan HOG detector
            # HOG detector yang digunakan dari dlib melalui library face_recognition
            faceCurrentFrame = face_recognition.face_locations(imgSmall)
            encodeCurrentFrame = face_recognition.face_encodings(
                imgSmall, faceCurrentFrame
            )

            imgBackground[162 : 162 + 480, 55 : 55 + 640] = img
            imgBackground[44 : 44 + 633, 808 : 808 + 414] = imgModeList[modeType]

            if faceCurrentFrame:
                for encodeFace, faceLocation in zip(
                    encodeCurrentFrame, faceCurrentFrame
                ):
                    # menampilkan wajah dan validasi
                    matches = face_recognition.compare_faces(
                        encodedFaceKnown, encodeFace
                    )
                    faceDistance = face_recognition.face_distance(
                        encodedFaceKnown, encodeFace
                    )

                    matchIndex = np.argmin(faceDistance)

                    y1, x2, y2, x1 = faceLocation
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4

                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1

                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                    # mengambil data mahasiswa jika wajah ditemukan
                    if matches[matchIndex] == True:
                        id = studentIDs[matchIndex]

                        if counter == 0:
                            cvzone.putTextRect(
                                imgBackground,
                                "Mendeteksi Wajah",
                                (65, 200),
                                thickness=2,
                            )
                            counter = 1
                            modeType = 1
                    else:
                        cvzone.putTextRect(
                            imgBackground,
                            "Wajah Tidak Dikenali",
                            (65, 200),
                            thickness=2,
                        )
                        # menunjukkan bahwa wajah tidak dikenali
                        modeType = 4
                        counter = 0
                        imgBackground[44 : 44 + 633, 808 : 808 + 414] = imgModeList[
                            modeType
                        ]

                if counter != 0:
                    if counter == 1:
                        studentInfo, imgStudent, secondElapsed = get_student_data(id)

                        # Check if student is registered for the subject
                        ref = db.reference(f"Students/{id}/subjects")
                        student_subjects = ref.get()

                        # Get subject code from selected_subject (assuming format "Nama Matkul (Kelas)")
                        subject_name, kelas = selected_subject.split(" (")
                        kelas = kelas.rstrip(")")

                        # Get subject code from Subjects database
                        subjects_ref = db.reference("Subjects")
                        all_subjects = subjects_ref.get()
                        subject_code = None

                        for code, info in all_subjects.items():
                            if info["name"] == subject_name and info["kelas"] == kelas:
                                subject_code = code
                                break

                        if not student_subjects or subject_code not in student_subjects:
                            modeType = 4  # Use error mode
                            counter = 0
                            cvzone.putTextRect(
                                imgBackground,
                                "Mahasiswa Tidak Terdaftar",
                                (65, 200),
                                thickness=2,
                                colorR=(0, 0, 255),  # Red text for error
                            )
                            
                        elif has_already_marked_attendance(id, selected_subject):
                            modeType = 3  # Mode for already marked attendance
                            counter = 0
                            cvzone.putTextRect(
                                imgBackground,
                                "Sudah Absen Hari Ini",
                                (65, 200),
                                thickness=2,
                            )
                        else:
                            # Mark attendance if not already done
                            if secondElapsed > 60:
                                ref = db.reference(f"Students/{id}")
                                studentInfo["total_attendance"] += 1
                                ref.child("total_attendance").set(
                                    studentInfo["total_attendance"]
                                )
                                ref.child("last_attendance_time").set(
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                )
                                mark_attendance(id, selected_subject)
                                # Display "Absensi Berhasil" text
                                cvzone.putTextRect(
                                    imgBackground,
                                    "Absensi Berhasil",
                                    (65, 300),
                                    scale=2,
                                    thickness=3,
                                    colorR=(0, 255, 0),  # Green text for success
                                )
                            else:
                                modeType = 3
                                counter = 0
                                imgBackground[44 : 44 + 633, 808 : 808 + 414] = (
                                    imgModeList[modeType]
                                )

                    if modeType != 3:
                        if 5 < counter <= 10:
                            modeType = 2

                        imgBackground[44 : 44 + 633, 808 : 808 + 414] = imgModeList[
                            modeType
                        ]

                        if counter <= 5:
                            cv2.putText(
                                imgBackground,
                                str(count_subject_attendance(id, subject_name, kelas)),
                                (861, 125),
                                cv2.FONT_HERSHEY_COMPLEX,
                                1,
                                (255, 255, 255),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(subject_name),
                                (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.5,
                                (255, 255, 255),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(id),
                                (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.5,
                                (255, 255, 255),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(kelas),
                                (910, 625),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.6,
                                (100, 100, 100),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["year"]),
                                (1025, 625),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.6,
                                (100, 100, 100),
                                1,
                            )
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["starting_year"]),
                                (1125, 625),
                                cv2.FONT_HERSHEY_COMPLEX,
                                0.6,
                                (100, 100, 100),
                                1,
                            )

                            (w, h), _ = cv2.getTextSize(
                                str(studentInfo["name"]), cv2.FONT_HERSHEY_COMPLEX, 1, 1
                            )

                            offset = (414 - w) // 2
                            cv2.putText(
                                imgBackground,
                                str(studentInfo["name"]),
                                (808 + offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX,
                                1,
                                (50, 50, 50),
                                1,
                            )

                            imgStudentResize = cv2.resize(imgStudent, (216, 216))

                            imgBackground[175 : 175 + 216, 909 : 909 + 216] = (
                                imgStudentResize
                            )

                        counter += 1

                        if counter >= 10:
                            counter = 0
                            modeType = 0
                            studentInfo = []
                            imgStudent = []
                            imgBackground[44 : 44 + 633, 808 : 808 + 414] = imgModeList[
                                modeType
                            ]

            else:
                modeType = 0
                counter = 0
            # menampilkan informamsi ke antarmuka
            ret, buffer = cv2.imencode(".jpeg", imgBackground)
            frame = buffer.tobytes()

        yield (b"--frame\r\n" b"Content-Type: image/jpeg \r\n\r\n" + frame + b"\r\n")
