from fastmcp import FastMCP
import sqlite3
import uuid
from datetime import datetime, date, timedelta

mcp_hospital = FastMCP(name="hospital-appointment-server")

# ── Database ──────────────────────────────────────────────────────────────────

DB_PATH = "db/hospital.sqlite3"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_hospital_db():
    print("Initialising hospital database...")
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                specialty TEXT NOT NULL,
                title TEXT NOT NULL,
                hospital TEXT NOT NULL,
                available_days TEXT NOT NULL,
                available_times TEXT NOT NULL,
                consultation_fee REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                gender TEXT NOT NULL,
                phone TEXT NOT NULL,
                id_number TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'scheduled',
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)

        if conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
            _insert_sample_data(conn)
        conn.commit()


def _insert_sample_data(conn):
    print("Inserting hospital sample data...")
    doctors = [
        ("D001", "Dr. Chen Wei",       "Cardiology",        "Chief Physician",     "City Central Hospital", "Mon,Tue,Thu,Fri", "09:00-12:00,14:00-17:00", 200.0),
        ("D002", "Dr. Liu Mei",        "Neurology",         "Associate Physician", "City Central Hospital", "Mon,Wed,Fri",     "08:30-11:30,13:30-16:30", 180.0),
        ("D003", "Dr. Zhang Hao",      "Orthopedics",       "Chief Physician",     "City Central Hospital", "Tue,Wed,Thu",     "09:00-12:00,14:00-17:00", 220.0),
        ("D004", "Dr. Wang Fang",      "Pediatrics",        "Attending Physician", "City Central Hospital", "Mon,Tue,Wed,Thu,Fri", "08:00-12:00",         150.0),
        ("D005", "Dr. Li Jian",        "General Surgery",   "Associate Physician", "City Central Hospital", "Mon,Wed,Fri",     "10:00-12:00,15:00-17:00", 160.0),
        ("D006", "Dr. Zhao Xin",       "Dermatology",       "Attending Physician", "City Central Hospital", "Tue,Thu,Fri",     "09:00-12:00",             120.0),
        ("D007", "Dr. Sun Ying",       "Ophthalmology",     "Chief Physician",     "City Central Hospital", "Mon,Tue,Thu",     "09:00-11:30,14:00-16:30", 180.0),
        ("D008", "Dr. Zhou Qiang",     "Internal Medicine", "Associate Physician", "City Central Hospital", "Mon,Tue,Wed,Thu,Fri", "08:00-12:00,14:00-17:00", 130.0),
    ]
    conn.executemany(
        "INSERT INTO doctors VALUES (?,?,?,?,?,?,?,?)", doctors
    )

    patients = [
        ("P001", "Alice Wong",   "1985-03-12", "Female", "138-0001-0001", "110101198503120011"),
        ("P002", "Bob Zhang",    "1992-07-25", "Male",   "139-0002-0002", "110101199207250021"),
        ("P003", "Carol Liu",    "1978-11-08", "Female", "137-0003-0003", "110101197811080031"),
        ("P004", "David Chen",   "2005-01-30", "Male",   "136-0004-0004", "110101200501300041"),
        ("P005", "Emily Wang",   "1965-05-20", "Female", "135-0005-0005", "110101196505200051"),
    ]
    conn.executemany(
        "INSERT INTO patients VALUES (?,?,?,?,?,?)", patients
    )

    today = date.today()
    appointments = [
        (str(uuid.uuid4()), "P001", "D001", str(today + timedelta(days=2)),  "10:00", "scheduled",  "Chest pain check-up",          datetime.now().isoformat(), None),
        (str(uuid.uuid4()), "P002", "D003", str(today + timedelta(days=3)),  "14:00", "scheduled",  "Knee pain evaluation",         datetime.now().isoformat(), None),
        (str(uuid.uuid4()), "P003", "D008", str(today - timedelta(days=5)),  "09:00", "completed",  "Annual physical examination",   datetime.now().isoformat(), "All results normal"),
        (str(uuid.uuid4()), "P004", "D004", str(today + timedelta(days=1)),  "08:30", "scheduled",  "Vaccination follow-up",        datetime.now().isoformat(), None),
        (str(uuid.uuid4()), "P005", "D002", str(today - timedelta(days=2)),  "14:30", "cancelled",  "Headache consultation",        datetime.now().isoformat(), "Patient rescheduled"),
        (str(uuid.uuid4()), "P001", "D008", str(today + timedelta(days=7)),  "09:30", "scheduled",  "Blood test review",            datetime.now().isoformat(), None),
    ]
    conn.executemany(
        "INSERT INTO appointments VALUES (?,?,?,?,?,?,?,?,?)", appointments
    )


# Initialise on import
init_hospital_db()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mask_id(id_number: str) -> str:
    if not id_number or len(id_number) < 8:
        return id_number
    return f"{id_number[:4]}{'*' * (len(id_number) - 8)}{id_number[-4:]}"


def _mask_phone(phone: str) -> str:
    digits = phone.replace("-", "")
    if len(digits) < 7:
        return phone
    return f"{digits[:3]}****{digits[-4:]}"


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp_hospital.tool(
    name="list_specialties",
    description="List all available medical specialties at the hospital. Returns a list of specialties and the number of doctors in each."
)
def list_specialties() -> str:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT specialty, COUNT(*) as cnt FROM doctors GROUP BY specialty ORDER BY specialty"
        ).fetchall()
    if not rows:
        return "No specialties found."
    lines = ["Available Medical Specialties:"]
    for specialty, cnt in rows:
        lines.append(f"  • {specialty} ({cnt} doctor{'s' if cnt > 1 else ''})")
    return "\n".join(lines)


@mcp_hospital.tool(
    name="list_doctors",
    description=(
        "List doctors at the hospital. "
        "Args: specialty (optional, filter by specialty e.g. 'Cardiology'). "
        "Returns doctor names, titles, specialties, available days, and consultation fees."
    )
)
def list_doctors(specialty: str = "") -> str:
    with get_conn() as conn:
        if specialty.strip():
            rows = conn.execute(
                "SELECT id, name, specialty, title, hospital, available_days, available_times, consultation_fee "
                "FROM doctors WHERE LOWER(specialty) = LOWER(?) ORDER BY name",
                (specialty.strip(),)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, specialty, title, hospital, available_days, available_times, consultation_fee "
                "FROM doctors ORDER BY specialty, name"
            ).fetchall()

    if not rows:
        return f"No doctors found{' for specialty: ' + specialty if specialty else ''}."

    lines = [f"Doctors{' — ' + specialty if specialty else ''}:"]
    for did, name, spec, title, hospital, avail_days, avail_times, fee in rows:
        lines.append(
            f"\n[{did}] {name} — {title}\n"
            f"  Specialty  : {spec}\n"
            f"  Hospital   : {hospital}\n"
            f"  Available  : {avail_days}  |  {avail_times}\n"
            f"  Fee        : ¥{fee:.0f}"
        )
    return "\n".join(lines)


@mcp_hospital.tool(
    name="get_doctor_schedule",
    description=(
        "Get a doctor's schedule and booked appointments for the next 7 days. "
        "Args: doctor_id (required, e.g. 'D001'). "
        "Returns the doctor's working days/times and existing bookings."
    )
)
def get_doctor_schedule(doctor_id: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, specialty, title, available_days, available_times FROM doctors WHERE id = ?",
            (doctor_id.strip(),)
        ).fetchone()
        if not row:
            return f"Error: Doctor {doctor_id} not found."

        _, name, specialty, title, avail_days, avail_times = row

        today = date.today()
        next_week = str(today + timedelta(days=7))
        bookings = conn.execute(
            "SELECT appointment_date, appointment_time, status FROM appointments "
            "WHERE doctor_id = ? AND appointment_date >= ? AND appointment_date <= ? AND status != 'cancelled' "
            "ORDER BY appointment_date, appointment_time",
            (doctor_id, str(today), next_week)
        ).fetchall()

    lines = [
        f"Schedule for {name} ({title}) — {specialty}",
        f"Working days : {avail_days}",
        f"Working hours: {avail_times}",
        f"\nBooked slots in the next 7 days:",
    ]
    if bookings:
        for appt_date, appt_time, status in bookings:
            lines.append(f"  • {appt_date} {appt_time}  [{status}]")
    else:
        lines.append("  (No bookings in the next 7 days)")

    return "\n".join(lines)


@mcp_hospital.tool(
    name="get_patient_info",
    description=(
        "Look up a patient record by name or patient ID. "
        "Args: query (patient name or patient ID, required). "
        "Returns patient details with masked sensitive fields."
    )
)
def get_patient_info(query: str) -> str:
    q = query.strip()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, date_of_birth, gender, phone, id_number FROM patients WHERE id = ? OR LOWER(name) = LOWER(?)",
            (q, q)
        ).fetchone()
    if not row:
        return f"Error: Patient '{query}' not found."

    pid, name, dob, gender, phone, id_num = row
    return (
        f"Patient ID  : {pid}\n"
        f"Name        : {name}\n"
        f"Date of Birth: {dob}\n"
        f"Gender      : {gender}\n"
        f"Phone       : {_mask_phone(phone)}\n"
        f"ID Number   : {_mask_id(id_num)}"
    )


@mcp_hospital.tool(
    name="book_appointment",
    description=(
        "Book a medical appointment. "
        "Args: patient_name (required), doctor_id (required, e.g. 'D001'), "
        "appointment_date (required, YYYY-MM-DD), appointment_time (required, HH:MM), "
        "reason (reason for visit, required). "
        "The patient must already exist in the system. "
        "Returns a confirmation with the appointment ID."
    )
)
def book_appointment(
    patient_name: str,
    doctor_id: str,
    appointment_date: str,
    appointment_time: str,
    reason: str,
) -> str:
    missing = [f for f, v in [
        ("patient_name", patient_name), ("doctor_id", doctor_id),
        ("appointment_date", appointment_date), ("appointment_time", appointment_time),
        ("reason", reason)
    ] if not v or not str(v).strip()]
    if missing:
        return f"Error: missing required fields: {', '.join(missing)}"

    # Validate date format
    try:
        appt_date = datetime.strptime(appointment_date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return "Error: appointment_date must be in YYYY-MM-DD format."

    if appt_date < date.today():
        return "Error: appointment_date cannot be in the past."

    # Validate time format
    try:
        datetime.strptime(appointment_time.strip(), "%H:%M")
    except ValueError:
        return "Error: appointment_time must be in HH:MM format."

    with get_conn() as conn:
        # Look up patient
        patient_row = conn.execute(
            "SELECT id, name FROM patients WHERE LOWER(name) = LOWER(?)",
            (patient_name.strip(),)
        ).fetchone()
        if not patient_row:
            return f"Error: Patient '{patient_name}' not found. Please register first."

        patient_id, pat_name = patient_row

        # Look up doctor
        doctor_row = conn.execute(
            "SELECT id, name, specialty, available_days, available_times, consultation_fee FROM doctors WHERE id = ?",
            (doctor_id.strip(),)
        ).fetchone()
        if not doctor_row:
            return f"Error: Doctor {doctor_id} not found."

        _, doc_name, specialty, avail_days, __, fee = doctor_row

        # Check doctor works on that weekday
        weekday = appt_date.strftime("%a")  # Mon, Tue, ...
        if weekday not in avail_days:
            return (
                f"Error: {doc_name} is not available on {weekday}. "
                f"Working days: {avail_days}."
            )

        # Check for time conflict (same doctor, date, time)
        conflict = conn.execute(
            "SELECT id FROM appointments WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ? AND status != 'cancelled'",
            (doctor_id, appointment_date.strip(), appointment_time.strip())
        ).fetchone()
        if conflict:
            return f"Error: {doc_name} already has a booking at {appointment_date} {appointment_time}. Please choose another time."

        # Create appointment
        appt_id = str(uuid.uuid4())[:8].upper()
        conn.execute(
            "INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, appointment_time, status, reason, created_at, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (appt_id, patient_id, doctor_id, appointment_date.strip(), appointment_time.strip(),
             "scheduled", reason.strip(), datetime.now().isoformat(), None)
        )
        conn.commit()

    return (
        f"Appointment booked successfully!\n"
        f"Appointment ID : {appt_id}\n"
        f"Patient        : {pat_name}\n"
        f"Doctor         : {doc_name} ({specialty})\n"
        f"Date & Time    : {appointment_date} {appointment_time}\n"
        f"Reason         : {reason}\n"
        f"Consultation Fee: ¥{fee:.0f}\n"
        f"Status         : Scheduled\n"
        f"Please arrive 15 minutes early and bring your ID card."
    )


@mcp_hospital.tool(
    name="cancel_appointment",
    description=(
        "Cancel an existing appointment. "
        "Args: appointment_id (required), reason (optional cancellation reason). "
        "Only 'scheduled' appointments can be cancelled."
    )
)
def cancel_appointment(appointment_id: str, reason: str = "") -> str:
    appt_id = appointment_id.strip().upper()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT a.id, a.status, a.appointment_date, a.appointment_time, d.name, p.name "
            "FROM appointments a "
            "JOIN doctors d ON a.doctor_id = d.id "
            "JOIN patients p ON a.patient_id = p.id "
            "WHERE a.id = ?",
            (appt_id,)
        ).fetchone()
        if not row:
            return f"Error: Appointment {appt_id} not found."

        _, status, appt_date, appt_time, doc_name, pat_name = row

        if status == "cancelled":
            return f"Appointment {appt_id} is already cancelled."
        if status == "completed":
            return f"Error: Cannot cancel a completed appointment."

        notes = f"Cancelled by patient. Reason: {reason}" if reason else "Cancelled by patient."
        conn.execute(
            "UPDATE appointments SET status = 'cancelled', notes = ? WHERE id = ?",
            (notes, appt_id)
        )
        conn.commit()

    return (
        f"Appointment {appt_id} has been cancelled.\n"
        f"Patient : {pat_name}\n"
        f"Doctor  : {doc_name}\n"
        f"Was scheduled for: {appt_date} {appt_time}"
    )


@mcp_hospital.tool(
    name="get_patient_appointments",
    description=(
        "Get all appointments for a patient. "
        "Args: patient_name (patient's full name, required), "
        "status_filter (optional: 'scheduled' / 'completed' / 'cancelled' / 'all', default 'all'). "
        "Returns a list of the patient's appointments with doctor and timing details."
    )
)
def get_patient_appointments(patient_name: str, status_filter: str = "all") -> str:
    with get_conn() as conn:
        patient_row = conn.execute(
            "SELECT id, name FROM patients WHERE LOWER(name) = LOWER(?)",
            (patient_name.strip(),)
        ).fetchone()
        if not patient_row:
            return f"Error: Patient '{patient_name}' not found."

        patient_id, pat_name = patient_row

        if status_filter.strip().lower() == "all":
            rows = conn.execute(
                "SELECT a.id, d.name, d.specialty, a.appointment_date, a.appointment_time, a.status, a.reason, a.notes "
                "FROM appointments a JOIN doctors d ON a.doctor_id = d.id "
                "WHERE a.patient_id = ? ORDER BY a.appointment_date DESC, a.appointment_time DESC",
                (patient_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT a.id, d.name, d.specialty, a.appointment_date, a.appointment_time, a.status, a.reason, a.notes "
                "FROM appointments a JOIN doctors d ON a.doctor_id = d.id "
                "WHERE a.patient_id = ? AND a.status = ? ORDER BY a.appointment_date DESC, a.appointment_time DESC",
                (patient_id, status_filter.strip().lower())
            ).fetchall()

    if not rows:
        return f"No appointments found for {pat_name}{' with status: ' + status_filter if status_filter != 'all' else ''}."

    lines = [f"Appointments for {pat_name}:"]
    for aid, doc_name, specialty, appt_date, appt_time, status, reason, notes in rows:
        lines.append(
            f"\n[{aid}] {appt_date} {appt_time}  —  [{status.upper()}]\n"
            f"  Doctor  : {doc_name} ({specialty})\n"
            f"  Reason  : {reason}"
        )
        if notes:
            lines.append(f"  Notes   : {notes}")
    return "\n".join(lines)


@mcp_hospital.tool(
    name="register_patient",
    description=(
        "Register a new patient in the hospital system. "
        "Args: name (full name, required), date_of_birth (YYYY-MM-DD, required), "
        "gender (Male/Female, required), phone (required), id_number (national ID, required). "
        "Returns the new patient ID on success."
    )
)
def register_patient(
    name: str,
    date_of_birth: str,
    gender: str,
    phone: str,
    id_number: str,
) -> str:
    missing = [f for f, v in [
        ("name", name), ("date_of_birth", date_of_birth),
        ("gender", gender), ("phone", phone), ("id_number", id_number)
    ] if not v or not str(v).strip()]
    if missing:
        return f"Error: missing required fields: {', '.join(missing)}"

    try:
        datetime.strptime(date_of_birth.strip(), "%Y-%m-%d")
    except ValueError:
        return "Error: date_of_birth must be in YYYY-MM-DD format."

    gender = gender.strip().capitalize()
    if gender not in ("Male", "Female"):
        return "Error: gender must be 'Male' or 'Female'."

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM patients WHERE LOWER(name) = LOWER(?) AND id_number = ?",
            (name.strip(), id_number.strip())
        ).fetchone()
        if existing:
            return f"Patient already registered with ID: {existing[0]}"

        patient_id = f"P{str(uuid.uuid4())[:6].upper()}"
        conn.execute(
            "INSERT INTO patients (id, name, date_of_birth, gender, phone, id_number) VALUES (?,?,?,?,?,?)",
            (patient_id, name.strip(), date_of_birth.strip(), gender, phone.strip(), id_number.strip())
        )
        conn.commit()

    return (
        f"Patient registered successfully!\n"
        f"Patient ID : {patient_id}\n"
        f"Name       : {name.strip()}\n"
        f"DOB        : {date_of_birth}\n"
        f"Gender     : {gender}\n"
        f"Phone      : {_mask_phone(phone)}"
    )
