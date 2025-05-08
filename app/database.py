from datetime import datetime

from firebase_admin import db, storage
import cv2
import numpy as np

BUCKET = storage.bucket()


def get_student_data(id):
    """Retrieve student data"""
    try:
        studentInfo = db.reference(f"Students/{id}").get()
        blob = BUCKET.get_blob(f"./app/static/Files/Images/{id}.png")
        array = np.frombuffer(blob.download_as_string(), np.uint8)
        imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
        datetimeObject = datetime.strptime(
            studentInfo["last_attendance_time"], "%Y-%m-%d %H:%M:%S"
        )
        secondElapsed = (datetime.now() - datetimeObject).total_seconds()
        return studentInfo, imgStudent, secondElapsed
    except Exception as e:
        print(f"Error fetching data for student {id}: {e}")
        return None, None, None


def get_admin_data(id):
    """Retrieve admin data"""
    try:
        adminInfo = db.reference(f"Admins/{id}").get()
        return adminInfo
    except Exception as e:
        print(f"Error fetching data for admin {id}: {e}")
        return None


def get_lecturer_data(id):
    """Retrieve lecturer data"""
    try:
        lecturerInfo = db.reference(f"Lecturers/{id}").get()
        return lecturerInfo
    except Exception as e:
        print(f"Error fetching data for lecturer {id}: {e}")
        return None


def get_logs_for_today():
    """Fetch attendance logs for today's date."""
    ref = db.reference("Logs")
    all_logs = ref.get()

    logs_for_day = {}
    date = datetime.now().date().isoformat()

    if not all_logs:
        return logs_for_day  # Return an empty dictionary if no logs exist

    # Loop through each student's logs
    for student_id, subjects in all_logs.items():
        for subject, records in subjects.items():
            for _, record_data in records.items():
                # Extract the date part from the time_attendance field
                time_attendance = record_data.get("time_attendance", "")
                if time_attendance.startswith(date):  # Check if it matches today's date
                    if student_id not in logs_for_day:
                        logs_for_day[student_id] = {}
                    if subject not in logs_for_day[student_id]:
                        logs_for_day[student_id][subject] = []

                    # Add the record to the logs_for_day dictionary
                    logs_for_day[student_id][subject].append(record_data)

    return logs_for_day


def delete_logs_for_today():
    """Delete attendance logs for today."""
    ref = db.reference("Logs")
    all_logs = ref.get()

    date = datetime.now().date().isoformat()

    if not all_logs:
        return  # No logs to delete

    # Loop through each student's logs
    for student_id, subjects in all_logs.items():
        for subject, records in subjects.items():
            for record_id, record_data in records.items():
                # Extract the date part from the time_attendance field
                time_attendance = record_data.get("time_attendance", "")
                if time_attendance.startswith(date):  # Check if it matches today's date
                    ref.child(f"{student_id}/{subject}/{record_id}").delete()
                    print(
                        f"Deleted record for student {student_id} in subject {subject}"
                    )

    print("Deletion complete.")
