import os
import json
import uuid

import pickle
from flask import (
    Blueprint,
    render_template,
    Response,
    redirect,
    url_for,
    request,
    session,
)
from firebase_admin import db

from .database import (
    get_student_data,
    get_lecturer_data,
    get_logs_for_today,
    delete_logs_for_today,
)
from .attendance import generate_frame
from .config import (
    ENCODE_FILE,
)
from .utils import (
    add_image_database,
    find_encodings,
    delete_image,
    count_subject_attendance,
)

bp = Blueprint("routes", __name__)


@bp.route("/")
def index():
    """Main page"""
    return render_template("index.html")


@bp.route("/lecturer_login", methods=["GET", "POST"])
def lecturer_login():
    """Lecturer login page"""
    if session.get("lecturer_id"):
        return redirect(url_for("routes.lecturer_dashboard"))
    # mengambil input form
    id = request.form.get("id_number", False)
    email = request.form.get("email", False)
    password = request.form.get("password", False)
    # mengambil dari database lecturer
    ref = db.reference(f"Lecturers").get()
    ids = []
    emails = []
    passwords = []
    for x in ref:
        # mencocokkan dengan database
        ids.append(ref[x]["id"])
        emails.append(ref[x]["email"])
        passwords.append(ref[x]["password"])
    if id:
        # periksa id, jika id tidak terdaftar tampilkan pesan
        if id not in ids:
            return render_template(
                "lecturer_login.html", data=" ❌ ID Tidak Terdaftar "
            )
        else:
            # Periksa Id dan email dari database lecturer
            if ref[id]["password"] == password and ref[id]["email"] == email:
                session["lecturer_id"] = id  # simpan id lecturer di session
                return redirect(url_for("routes.lecturer_dashboard"))
            else:
                id = False
                return render_template(
                    "lecturer_login.html", data=" ❌ Email/Password Salah"
                )
    else:
        return render_template("lecturer_login.html")


@bp.route("/student_login", methods=["GET", "POST"])
def student_login():
    """Student login page"""
    if session.get("student_id"):
        return redirect(url_for("routes.student_dashboard"))
    # mengambil input form
    id = request.form.get("id_number", False)
    email = request.form.get("email", False)
    password = request.form.get("password", False)
    # memuat database
    studentIDs, _ = add_image_database()
    # mencocokkan dengan database
    if id:
        if id not in studentIDs:
            return render_template("student_login.html", data=" ❌ ID Tidak Terdaftar")
        else:
            if (
                get_student_data(id)[0]["password"] == password
                and get_student_data(id)[0]["email"] == email
            ):
                session["student_id"] = id  # simpan id student di session
                return redirect(url_for("routes.student_dashboard"))
            else:
                id = False
                return render_template(
                    "student_login.html", data=" ❌ Email/Password Salah"
                )
    else:
        return render_template("student_login.html")


@bp.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    """Admin login page"""
    if session.get("admin_id"):
        return redirect(url_for("routes.admin_dashboard"))
    # mengambil input form
    id = request.form.get("id_number", False)
    email = request.form.get("email", False)
    password = request.form.get("password", False)
    # mengambil dari database admin
    ref = db.reference(f"Admins").get()
    ids = []
    emails = []
    passwords = []
    for x in ref:
        # mencocokkan dengan database
        ids.append(ref[x]["id"])
        emails.append(ref[x]["email"])
        passwords.append(ref[x]["password"])
    if id:
        # periksa id, jika id tidak terdaftar tampilkan pesan
        if id not in ids:
            return render_template("admin_login.html", data=" ❌ ID Tidak Terdaftar ")
        else:
            # Periksa Id dan email dari database admin
            if ref[id]["password"] == password and ref[id]["email"] == email:
                session["admin_id"] = id  # simpan id a di session
                return redirect(url_for("routes.admin_dashboard"))
            else:
                id = False
                return render_template(
                    "admin_login.html", data=" ❌ Email/Password Salah"
                )
    else:
        return render_template("admin_login.html")


@bp.route("/video")
def video():
    """Stream video for face recognition"""
    if "selected_subject" not in session:
        return redirect(url_for("routes.choose_subject"))
    selected_subject = session.get("selected_subject")
    return Response(
        generate_frame(selected_subject),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@bp.route("/logout")
def logout():
    """Log the user out by clearing the session."""
    session.clear()  # Clear all session data
    return redirect(url_for("routes.index"))


@bp.route("/student_dashboard", methods=["GET", "POST"])
def student_dashboard():
    """Show student dashboard."""
    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("routes.student_login"))

    studentInfo, imgStudent, secondElapsed = get_student_data(student_id)
    hoursElapsed = round((secondElapsed / 3600), 2)
    subjects = []
    ref = db.reference(f"Subjects").get()
    if ref is not None:
        for i in ref:
            subjects.append(ref[i])

    if request.method == "POST":
        selected_subject_id = request.form.get("subject")
        if selected_subject_id and selected_subject_id != "0":
            # Get subject details from Subjects collection
            subject_ref = db.reference(f"Subjects/{selected_subject_id}").get()

            if subject_ref:
                subject_info = {
                    "id": selected_subject_id,
                    "code": subject_ref.get("code"),
                    "name": subject_ref.get("name"),
                    "kelas": subject_ref.get("kelas"),
                    "lecturer": subject_ref.get("lecturer"),
                    "lecturer_id": subject_ref.get("lecturer_id"),
                }

                # Get current student data
                student_ref = db.reference(f"Students/{student_id}")
                current_student = student_ref.get()

                # Initialize or update subjects list
                if current_student:
                    current_subjects = current_student.get("subjects", {})

                    # Check if the subject code already exists in the student's subjects
                    subject_code = subject_info["code"]
                    for (
                        existing_subject_id,
                        existing_subject_data,
                    ) in current_subjects.items():
                        if existing_subject_data["code"] == subject_code:
                            return render_template(
                                "student.html",
                                data={
                                    "studentInfo": studentInfo,
                                    "lastLogin": hoursElapsed,
                                    "image": imgStudent,
                                    "subjects": subjects,
                                    "error": f"Mata kuliah {existing_subject_data['name']} sudah diambil!",
                                },
                            )
                    else:
                        # Jika belum ada, tambahkan mata kuliah
                        current_subjects[selected_subject_id] = subject_info
                        student_ref.update({"subjects": current_subjects})
                        return redirect(url_for("routes.student_dashboard"))

    info = {
        "studentInfo": studentInfo,
        "lastLogin": hoursElapsed,
        "image": imgStudent,
        "subjects": subjects,
    }
    return render_template("student.html", data=info)


@bp.route("/student_attendance_list")
def student_attendance_list():
    """Show student attendance list."""
    student_info = []
    logs = get_logs_for_today()
    if logs:
        student_info = []
        for student_id, subjects in logs.items():
            for subject, records in subjects.items():
                for record in records:
                    info = get_student_data(student_id)
                    student_info.append(
                        {
                            "subject": subject,
                            "info": {
                                "id": student_id,
                                "name": info[0]["name"],
                                "total_attendance": record.get("total_attendance"),
                                "last_attendance_time": record.get("time_attendance"),
                            },
                        }
                    )
    return render_template("student_attendance_list.html", data=student_info)


@bp.route("/lecturer/choose_subject", methods=["GET", "POST"])
def choose_subject():
    """Let users choose a subject."""
    lecturer_id = session.get("lecturer_id")
    if not lecturer_id:
        return redirect(url_for("routes.lecturer_login"))
    subjects = {}
    ref = db.reference(f"Subjects").get()
    if ref is not None:
        for i in ref:
            lecturer = ref[i].get("lecturer")
            if lecturer == get_lecturer_data(lecturer_id)["name"]:
                subjects[i] = ref[i]
    if request.method == "POST":
        subject = request.form.get("subject")
        if subject:
            session["selected_subject"] = subject
            return redirect(url_for("routes.absensi"))
    return render_template("choose_subject.html", subjects=subjects)


@bp.route("/lecturer/absensi", methods=["GET", "POST"])
def absensi():
    """Show attendance page."""
    lecturer_id = session.get("lecturer_id")
    if not lecturer_id:
        return redirect(url_for("routes.lecturer_login"))
    if "selected_subject" not in session:
        return redirect(url_for("routes.choose_subject"))
    subject = session.get("selected_subject")
    return render_template("absensi.html", subject=subject)


@bp.route("/lecturer")
def lecturer_dashboard():
    """Show lecturer dashboard."""
    lecturer_id = session.get("lecturer_id")
    if not lecturer_id:
        return redirect(url_for("routes.lecturer_login"))

    subjects = {}
    ref = db.reference(f"Subjects").get()
    if ref is not None:
        for i in ref:
            lecturer = ref[i].get("lecturer")
            if lecturer == get_lecturer_data(lecturer_id)["name"]:
                subjects[i] = ref[i]
    return render_template("lecturer.html", data={"subjects": subjects})


@bp.route("/lecturer/student_list", methods=["GET", "POST"])
def lecturer_student_list():
    """Show student list of a subject."""
    lecturer_id = session.get("lecturer_id")
    if not lecturer_id:
        return redirect(url_for("routes.lecturer_login"))

    subject_id = request.form.get("subject_id")
    if not subject_id:
        return redirect(url_for("routes.lecturer_dashboard"))

    # Get subject details
    subject_ref = db.reference(f"Subjects/{subject_id}").get()
    if not subject_ref:
        return redirect(url_for("routes.lecturer_dashboard"))

    subject_code = subject_ref.get("subject_id")
    subject_info = {
        "code": subject_code,
        "name": subject_ref.get("name"),
        "kelas": subject_ref.get("kelas"),
        "lecturer": subject_ref.get("lecturer"),
    }

    # Get all students and filter those enrolled in this subject
    students_ref = db.reference("Students").get()
    filtered_students = []

    if students_ref:
        for student_id, student_data in students_ref.items():
            student_subjects = student_data.get("subjects", {})
            # Check if student is enrolled in this subject
            if subject_code in student_subjects:
                student_info, img_student, seconds_elapsed = get_student_data(
                    student_id
                )
                filtered_students.append({"info": student_info, "image": img_student})

    return render_template(
        "lecturer_student_list.html",
        data={"students": filtered_students, "subject": subject_info},
    )


@bp.route("/admin")
def admin_dashboard():
    """Show admin dashboard."""
    admin_id = session.get("admin_id")
    if not admin_id:
        return redirect(url_for("routes.admin_login"))
    all_student_info = []
    studentIDs, _ = add_image_database()
    for i in studentIDs:
        all_student_info.append(get_student_data(i))
    return render_template("admin.html", data=all_student_info)


@bp.route("/admin/lecturer_data")
def lecturer_data():
    """Show admin dashboard."""
    admin_id = session.get("admin_id")
    if not admin_id:
        return redirect(url_for("routes.admin_login"))
    all_lecturer_info = []
    ref = db.reference(f"Lecturers").get()
    if ref is not None:
        for i in ref:
            all_lecturer_info.append(ref[i])
    return render_template("lecturer_data.html", data=all_lecturer_info)


@bp.route("/admin/subject_data")
def subject_data():
    """Show subject data."""
    admin_id = session.get("admin_id")
    if not admin_id:
        return redirect(url_for("routes.admin_login"))
    all_subject_info = []
    ref = db.reference(f"Subjects").get()
    if ref is not None:
        for i in ref:
            all_subject_info.append(ref[i])
    return render_template("subject_data.html", data=all_subject_info)


@bp.route("/lecturer/lecturer_attendance_list", methods=["GET", "POST"])
def lecturer_attendance_list():
    # Check if lecturer is logged in
    lecturer_id = session.get("lecturer_id")
    if not lecturer_id:
        return redirect(url_for("routes.lecturer_login"))

    # Initialize empty student info list
    student_info = []

    # Handle POST request for deleting logs
    if request.method == "POST":
        if request.form.get("button_lecturer") == "VALUE2":
            try:
                delete_logs_for_today()
            except Exception as e:
                print(f"Terjadi kesalahan saat menghapus data kehadiran: {str(e)}")
            return redirect(url_for("routes.lecturer_attendance_list"))

    # Get and process attendance logs
    try:
        logs = get_logs_for_today()
        print(f"Data kehadiran hari ini: {logs}")
        if logs:
            for student_id, subjects in logs.items():
                for subject, records in subjects.items():
                    for record in records:
                        info = get_student_data(student_id)
                        if info:  # Make sure we got valid student data
                            student_info.append(
                                {
                                    "subject": subject,
                                    "info": {
                                        "id": student_id,
                                        "name": info[0]["name"],
                                        "total_attendance": record.get(
                                            "total_attendance"
                                        ),
                                        "last_attendance_time": record.get(
                                            "time_attendance"
                                        ),
                                    },
                                }
                            )
    except Exception as e:
        print(f"Terjadi kesalahan saat memproses data kehadiran: {str(e)}")
    # Render template with gathered data
    return render_template("lecturer_attendance_list.html", data=student_info)


@bp.route("/admin/add_student", methods=["GET", "POST"])
def add_student():
    admin_id = session.get("admin_id")
    if not admin_id:
        return redirect(url_for("routes.admin_login"))
    id = request.form.get("id", False)
    name = request.form.get("name", False)
    password = request.form.get("password", False)
    dob = request.form.get("dob", False)
    city = request.form.get("city", False)
    country = request.form.get("province", False)
    phone = request.form.get("phone", False)
    email = request.form.get("email", False)
    starting_year = request.form.get("starting_year", False)
    total_attendance = request.form.get("total_attendance", False)
    year = request.form.get("year", False)
    last_attendance_date = request.form.get("last_attendance_date", False)
    last_attendance_time = request.form.get("last_attendance_time", False)

    address = f"{city}, {country}"
    last_attendance_datetime = f"{last_attendance_date} {last_attendance_time}:00"
    year = int(year)
    total_attendance = int(total_attendance)
    starting_year = int(starting_year)

    if request.method == "POST":
        image = request.files["image"]
        filename = f"{'./app/static/Files/Images'}/{id}.png"
        image.save(os.path.join(filename))

    studentIDs, imgList = add_image_database()

    encodeListKnown = find_encodings(imgList)

    encodeListKnownWithIds = [encodeListKnown, studentIDs]

    file = open(ENCODE_FILE, "wb")
    pickle.dump(encodeListKnownWithIds, file)  # Menyimpan encoding wajah
    file.close()

    if id:
        add_student = db.reference(f"Students")

        add_student.child(id).set(
            {
                "id": id,
                "name": name,
                "password": password,
                "dob": dob,
                "address": address,
                "phone": phone,
                "email": email,
                "starting_year": starting_year,
                "total_attendance": total_attendance,
                "year": year,
                "last_attendance_time": last_attendance_datetime,
            }
        )
        return redirect(url_for("routes.admin_dashboard"))

    return render_template("add_student.html")


@bp.route("/admin/add_lecturer", methods=["GET", "POST"])
def add_lecturer():
    admin_id = session.get("admin_id")
    if not admin_id:
        return redirect(url_for("routes.admin_login"))
    id = request.form.get("id", False)
    name = request.form.get("name", False)
    password = request.form.get("password", False)
    city = request.form.get("city", False)
    country = request.form.get("province", False)
    email = request.form.get("email", False)
    major = request.form.get("major", False)

    address = f"{city}, {country}"

    if id:
        add_lecturer = db.reference(f"Lecturers")

        add_lecturer.child(id).set(
            {
                "id": id,
                "name": name,
                "password": password,
                "address": address,
                "email": email,
                "major": major,
            }
        )
        return redirect(url_for("routes.lecturer_data"))

    return render_template("add_lecturer.html")


@bp.route("/admin/add_subject", methods=["GET", "POST"])
def add_subject():
    admin_id = session.get("admin_id")
    if not admin_id:
        return redirect(url_for("routes.admin_login"))
    code = request.form.get("code", False)
    name = request.form.get("name", False)
    lecturer = request.form.get("lecturer", False)
    kelas = request.form.get("kelas", False)

    # Get all lecturers for the dropdown
    lecturers = []
    lecturer_refs = {}  # Store lecturer references
    ref = db.reference("Lecturers").get()
    if ref:
        for lecturer_id, lecturer_data in ref.items():
            lecturers.append(lecturer_data["name"])
            lecturer_refs[lecturer_data["name"]] = lecturer_id

    if code:
        # Check if the combination of code and class already exists
        subjects_ref = db.reference("Subjects")
        existing_subjects = subjects_ref.get()

        if existing_subjects:
            for subject in existing_subjects.values():
                if subject["code"] == code and subject["kelas"] == kelas:
                    # If combination exists, return error
                    error_message = f"Kode {code} sudah terdaftar untuk kelas {kelas}"
                    return render_template(
                        "add_subject.html", lecturers=lecturers, error=error_message
                    )

        subject_id = str(uuid.uuid4())  # Generate a unique subject ID
        add_subject = db.reference(f"Subjects/{subject_id}")  # Store by subject ID
        add_subject.set(
            {
                "subject_id": subject_id,
                "code": code,
                "name": name,
                "lecturer_id": lecturer_refs.get(lecturer, ""),
                "lecturer": lecturer,
                "kelas": kelas,
            }
        )

        # Update lecturer's subjects
        if lecturer in lecturer_refs:
            lecturer_id = lecturer_refs[lecturer]
            lecturer_ref = db.reference(f"Lecturers/{lecturer_id}")
            lecturer_data = lecturer_ref.get()

            existing_subjects = lecturer_data.get("subjects", {})

            subject_info = {
                "id": subject_id,
                "code": code,
                "name": name,
                "kelas": kelas,
            }

            if code not in existing_subjects:
                existing_subjects[subject_id] = subject_info
                lecturer_ref.update({"subjects": existing_subjects})

        return redirect(url_for("routes.subject_data"))

    return render_template("add_subject.html", lecturers=lecturers)


@bp.route("/admin/edit_student", methods=["POST", "GET"])
def admin_edit_student():
    if not session.get("admin_id"):
        return redirect(url_for("routes.admin_login"))
    value = request.form.get("edit_student")

    studentInfo, imgStudent, secondElapsed = get_student_data(value)
    hoursElapsed = round((secondElapsed / 3600), 2)

    info = {
        "studentInfo": studentInfo,
        "lastLogin": hoursElapsed,
        "image": imgStudent,
    }

    return render_template("admin_edit_student.html", data=info)


@bp.route("/lecturer/edit_student", methods=["POST", "GET"])
def lecturer_edit_student():
    if not session.get("lecturer_id"):
        return redirect(url_for("routes.lecturer_login"))

    student_id = request.form.get("edit_student")
    subject_name = request.form.get("subject_name")
    subject_class = request.form.get("subject_class")

    # Get student info and image
    studentInfo, imgStudent, secondElapsed = get_student_data(student_id)
    hoursElapsed = round((secondElapsed / 3600), 2)

    # Get attendance count
    total_attendance = count_subject_attendance(student_id, subject_name, subject_class)

    info = {
        "studentInfo": studentInfo,
        "totalAttendance": total_attendance,
        "lastLogin": hoursElapsed,
        "image": imgStudent,
    }

    return render_template("lecturer_edit_student.html", data=info)


@bp.route("/admin/edit_lecturer", methods=["POST", "GET"])
def admin_edit_lecturer():
    if not session.get("admin_id"):
        return redirect(url_for("routes.admin_login"))
    value = request.form.get("edit_lecturer")
    lecturer_data = get_lecturer_data(value)
    return render_template("admin_edit_lecturer.html", data=lecturer_data)


@bp.route("/save_changes_student", methods=["POST"])
def save_changes_student():
    content = request.get_data()

    dic_data = json.loads(content.decode("utf-8"))

    dic_data = {k: v.strip() for k, v in dic_data.items()}

    dic_data["year"] = int(dic_data["year"])
    dic_data["total_attendance"] = int(dic_data["total_attendance"])
    dic_data["starting_year"] = int(dic_data["starting_year"])

    update_student = db.reference(f"Students")

    update_student.child(dic_data["id"]).update(
        {
            "id": dic_data["id"],
            "name": dic_data["name"],
            "dob": dic_data["dob"],
            "address": dic_data["address"],
            "phone": dic_data["phone"],
            "email": dic_data["email"],
            "starting_year": dic_data["starting_year"],
            "total_attendance": dic_data["total_attendance"],
            "year": dic_data["year"],
            "last_attendance_time": dic_data["last_attendance_time"],
        }
    )
    return "Data received successfully!"


@bp.route("/save_changes_lecturer", methods=["POST", "GET"])
def save_changes_lecturer():
    content = request.get_data()

    dic_data = json.loads(content.decode("utf-8"))

    dic_data = {k: v.strip() for k, v in dic_data.items()}

    update_lecturer = db.reference(f"Lecturers")

    update_lecturer.child(dic_data["id"]).update(
        {
            "id": dic_data["id"],
            "name": dic_data["name"],
            "address": dic_data["address"],
            "email": dic_data["email"],
            "major": dic_data["major"],
        }
    )
    return "Data received successfully!"


@bp.route("/delete_student", methods=["POST", "GET"])
def delete_student():
    print("Mencoba menghapus mahasiswa...")  # Debug log
    content = request.get_json()
    student_id = content.get("student_id")
    print(f"ID Mahasiswa yang akan dihapus: {student_id}")  # Debug log
    try:
        delete_student = db.reference(f"Students")
        delete_student.child(student_id).delete()
        print(f"Data mahasiswa berhasil dihapus dari database")  # Debug log

        delete_image(student_id)
        print(f"Gambar mahasiswa berhasil dihapus")  # Debug log

        studentIDs, imgList = add_image_database()
        encodeListKnown = find_encodings(imgList)
        encodeListKnownWithIds = [encodeListKnown, studentIDs]

        file = open(ENCODE_FILE, "wb")
        pickle.dump(encodeListKnownWithIds, file)
        file.close()
        print(f"Encoding berhasil diupdate")  # Debug log

        return "Success", 200
    except Exception as e:
        print(f"Terjadi error: {str(e)}")  # Debug log
        return str(e), 500


@bp.route("/delete_subject/<subject_id>", methods=["POST"])
def delete_subject(subject_id):
    print(f"Mencoba menghapus mata kuliah dengan ID: {subject_id}")

    try:
        # 1. Verifikasi mata kuliah ada di database
        subjects_ref = db.reference("Subjects")
        subject_data = subjects_ref.child(subject_id).get()

        if not subject_data:
            return "Mata kuliah tidak ditemukan", 404

        print(f"Data Mata Kuliah yang ditemukan: {subject_data}")

        # 2. Hapus mata kuliah dari semua dosen
        lecturer_ref = db.reference("Lecturers")
        lecturer_data = lecturer_ref.get()

        if lecturer_data:
            for lecturer_id, lecturer in lecturer_data.items():
                if isinstance(lecturer, dict) and "subjects" in lecturer:
                    updated_subjects = {
                        sub_id: sub_info
                        for sub_id, sub_info in lecturer["subjects"].items()
                        if sub_id != subject_id
                    }

                    lecturer_ref.child(lecturer_id).update(
                        {"subjects": updated_subjects}
                    )
                    print(
                        f"Mata kuliah {subject_id} berhasil dihapus dari dosen {lecturer_id}"
                    )

        # 3. Hapus mata kuliah dari semua mahasiswa
        student_ref = db.reference("Students")
        student_data = student_ref.get()

        if student_data:
            for student_id, student in student_data.items():
                if isinstance(student, dict) and "subjects" in student:
                    updated_subjects = {
                        sub_id: sub_info
                        for sub_id, sub_info in student["subjects"].items()
                        if sub_id != subject_id
                    }

                    student_ref.child(student_id).update({"subjects": updated_subjects})
                    print(
                        f"Mata kuliah {subject_id} berhasil dihapus dari mahasiswa {student_id}"
                    )

        # 4. Hapus mata kuliah dari database Subjects
        subjects_ref.child(subject_id).delete()
        print(f"Data mata kuliah {subject_id} berhasil dihapus dari database")

        return "Success", 200

    except Exception as e:
        print(f"Terjadi error: {str(e)}")
        return str(e), 500


@bp.route("/delete_student_subject/<subject_id>", methods=["POST"])
def delete_student_subject(subject_id):
    print("Mencoba menghapus mata kuliah mahasiswa...")

    student_id = session.get("student_id")
    if not student_id:
        return {"error": "Unauthorized: Student ID not found in session"}, 401

    print(f"ID Mahasiswa: {student_id}")
    print(f"Kode Mata Kuliah yang akan dihapus: {subject_id}")

    try:
        # Referensi ke data mahasiswa di Firebase
        student_ref = db.reference(f"Students/{student_id}")
        student_data = student_ref.get()

        if not student_data:
            return {"error": "Data mahasiswa tidak ditemukan"}, 404

        # Pastikan subjects ada dan berbentuk dictionary
        subjects = student_data.get("subjects", {})
        if not isinstance(subjects, dict):
            return {"error": "Format data subjects tidak valid"}, 500

        # Cek apakah subject_id ada dalam subjects
        if subject_id not in subjects:
            return {"error": "Mata kuliah tidak ditemukan dalam daftar mahasiswa"}, 404

        # Hapus mata kuliah berdasarkan subject_id
        del subjects[subject_id]

        # Perbarui data mahasiswa di database
        student_ref.update({"subjects": subjects})

        print(f"Mata kuliah {subject_id} berhasil dihapus untuk mahasiswa {student_id}")
        return {"message": "Mata kuliah berhasil dihapus"}, 200

    except Exception as e:
        print(f"Terjadi error: {str(e)}")
        return {"error": str(e)}, 500


@bp.route("/delete_lecturer", methods=["POST", "GET"])
def delete_lecturer():
    print("Mencoba menghapus dosen...")  # Debug log
    content = request.get_json()
    lecture_id = content.get("lecture_id")
    print(f"ID Dosen yang akan dihapus: {lecture_id}")  # Debug log
    try:
        delete_lecturer = db.reference(f"Lecturers")
        delete_lecturer.child(lecture_id).delete()
        print(f"Data dosen berhasil dihapus dari database")  # Debug log

        delete_subjects = db.reference(f"Subjects").get()
        for i in delete_subjects:
            if delete_subjects[i].get("lecturer") == lecture_id:
                delete_subjects.pop(i)
        db.reference(f"Subjects").set(delete_subjects)
        print(f"Data mata kuliah dosen berhasil dihapus dari database")  # Debug log

        return "Success", 200
    except Exception as e:
        print(f"Terjadi error: {str(e)}")  # Debug log
        return str(e), 500
