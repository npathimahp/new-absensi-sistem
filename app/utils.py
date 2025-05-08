from datetime import datetime
import os

from firebase_admin import db, storage
import face_recognition
import cv2


def has_already_marked_attendance(student_id, subject):
    """Check if the student has already marked attendance today."""
    today = datetime.now().date().isoformat()  # Format today's date as a string
    ref = db.reference(f"Logs/{student_id}/{subject}")
    attendance_records = ref.get()

    if attendance_records:
        for _, record_data in attendance_records.items():
            # Check if any record matches today's date
            time_attendance = record_data.get("time_attendance", "")
            if time_attendance.startswith(today):
                return True
    return False


def mark_attendance(student_id, subject):
    """Mark attendance for the student and update total attendance."""
    today = datetime.now().date().isoformat()  # Current date in YYYY-MM-DD format
    now = datetime.now().isoformat()  # Current time in ISO format

    # Reference to the Firebase path for the student's subject attendance
    ref = db.reference(f"Logs/{student_id}/{subject}")
    attendance_records = ref.get()

    # Determine the next "Pertemuan" (meeting number)
    if attendance_records:
        # Sort by pertemuan keys to get the last meeting
        sorted_meetings = sorted(attendance_records.items(), key=lambda x: x[0])
        last_meeting_key, last_meeting_data = sorted_meetings[-1]
        last_attendance_date = last_meeting_data["time_attendance"].split("T")[0]

        if last_attendance_date != today:
            # If the last attendance date is not today, create a new meeting entry
            next_meeting_number = int(last_meeting_key.split()[-1]) + 1
            new_meeting_key = f"Pertemuan {next_meeting_number}"
            total_attendance = last_meeting_data["total_attendance"] + 1
        else:
            # Attendance already marked today, return False
            return False
    else:
        # No records exist, start with "Pertemuan 1"
        new_meeting_key = "Pertemuan 1"
        total_attendance = 1

    # Create or update the attendance entry
    attendance_entry = {
        "time_attendance": now,
        "total_attendance": total_attendance,
    }

    # Save the new meeting record
    ref.child(new_meeting_key).set(attendance_entry)

    return True


def add_image_database():
    """Add images to the database and return the list of student IDs."""
    folderPath = "./app/static/Files/Images"
    imgPathList = os.listdir(folderPath)
    imgList = []
    studentIDs = []

    for path in imgPathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        studentIDs.append(os.path.splitext(path)[0])
        # mengunggah gambar ke firebase
        fileName = f"{folderPath}/{path}"
        bucket = storage.bucket()
        blob = bucket.blob(fileName)
        blob.upload_from_filename(fileName)

    return studentIDs, imgList


def delete_image(student_id):
    """Delete the image from the database and the local storage."""
    filepath = f"./app/static/Files/Images/{student_id}.png"
    os.remove(filepath)  # hapus dari penyimpanan lokal

    bucket = storage.bucket()
    blob = bucket.blob(filepath)
    blob.delete()  # hapus dari penyimpanan firebase

    return True


def find_encodings(images):
    """Find the encodings of the images."""
    encodeList = []

    for img in images:
        # mengonversi gambar dari BGR ke RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList


def format_datetime(value):
    """Format the datetime string to a human-readable format"""
    try:
        # Parse string into a datetime object
        dt = datetime.fromisoformat(value)
        # Format to desired human-readable string
        return dt.strftime("%d %B %Y, %I:%M %p")
    except (ValueError, TypeError):
        return "N/A"  # Default if the format is incorrect or value is None


def count_subject_attendance(student_id, subject_name, subject_class):
    """
    Count total attendance for a specific student in a specific subject
    Returns the total number of attendances
    """
    try:
        # Format subject identifier as "name (class)"
        subject_identifier = f"{subject_name} ({subject_class})"

        # Get logs for the student
        logs_ref = db.reference(f"Logs/{student_id}")
        student_logs = logs_ref.get()

        if not student_logs or subject_identifier not in student_logs:
            return 0

        # Count total meetings for the subject
        total_attendance = len(student_logs[subject_identifier])

        return total_attendance

    except Exception as e:
        print(f"Error counting attendance: {str(e)}")
        return 0
