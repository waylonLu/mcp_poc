import json
from fastmcp import FastMCP
from datetime import datetime, date
from db.hospital_db import hospital_db

mcp_hospital = FastMCP(name="hospital-appointment-server")


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


def _ok(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _err(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp_hospital.tool(
    name="hospital_list_specialties",
    description=(
        "Use this tool when the user wants to browse available medical departments or specialties "
        "at the hospital, or when they need to know which specialty to choose before looking up doctors. "
        "Do NOT use this tool when the user already knows the specialty and wants to find a specific doctor "
        "— use hospital_list_doctors instead. "
        "Returns a structured list of specialties with doctor counts."
    )
)
def hospital_list_specialties() -> str:
    rows = hospital_db.get_specialties()
    if not rows:
        return _err("No specialties found.")
    return _ok({
        "specialties": [
            {"name": specialty, "doctor_count": cnt}
            for specialty, cnt in rows
        ]
    })


@mcp_hospital.tool(
    name="hospital_list_doctors",
    description=(
        "Use this tool when the user wants to find doctors, browse doctor profiles, check availability, "
        "or compare consultation fees. Accepts an optional specialty filter. "
        "Do NOT use this tool to check a specific doctor's booked schedule or time slots — "
        "use hospital_get_doctor_schedule for that. "
        "Returns doctor_id (required for booking), name, title, specialty, available days/times, and fee."
    )
)
def hospital_list_doctors(specialty: str = "") -> str:
    rows = hospital_db.get_doctors(specialty)
    if not rows:
        return _err(f"No doctors found{' for specialty: ' + specialty if specialty else ''}.")
    return _ok({
        "doctors": [
            {
                "doctor_id": did,
                "name": name,
                "title": title,
                "specialty": spec,
                "hospital": hosp,
                "available_days": avail_days.split(","),
                "available_times": avail_times.split(","),
                "consultation_fee": fee,
            }
            for did, name, spec, title, hosp, avail_days, avail_times, fee in rows
        ]
    })


@mcp_hospital.tool(
    name="hospital_get_doctor_schedule",
    description=(
        "Use this tool when the user wants to check a specific doctor's booked time slots for the next 7 days "
        "to find an available appointment time. Requires a doctor_id (e.g. 'D001'). "
        "Do NOT use this tool to list all doctors or browse specialties — "
        "use hospital_list_doctors or hospital_list_specialties for that. "
        "Returns the doctor's working days, hours, and already-booked slots."
    )
)
def hospital_get_doctor_schedule(doctor_id: str) -> str:
    row = hospital_db.get_doctor(doctor_id)
    if not row:
        return _err(f"Doctor {doctor_id} not found.")

    did, name, specialty, title, avail_days, avail_times, fee = row
    bookings = hospital_db.get_doctor_bookings(doctor_id)

    return _ok({
        "doctor_id": did,
        "name": name,
        "title": title,
        "specialty": specialty,
        "consultation_fee": fee,
        "working_days": avail_days.split(","),
        "working_hours": avail_times.split(","),
        "booked_slots_next_7_days": [
            {"date": d, "time": t, "status": s}
            for d, t, s in bookings
        ],
    })


@mcp_hospital.tool(
    name="hospital_get_patient_info",
    description=(
        "Use this tool when the user wants to look up an existing patient's profile by name or patient ID. "
        "Do NOT use this tool to register a new patient — use hospital_register_patient for that. "
        "Do NOT use this tool to list a patient's appointments — use hospital_get_patient_appointments. "
        "Sensitive fields (phone, ID number) are masked. Returns patient_id for use in other tools."
    )
)
def hospital_get_patient_info(query: str) -> str:
    row = hospital_db.get_patient(query.strip())
    if not row:
        return _err(f"Patient '{query}' not found.")

    pid, name, dob, gender, phone, id_num = row
    return _ok({
        "patient_id": pid,
        "name": name,
        "date_of_birth": dob,
        "gender": gender,
        "phone": _mask_phone(phone),
        "id_number": _mask_id(id_num),
    })


@mcp_hospital.tool(
    name="hospital_book_appointment",
    description=(
        "Use this tool when the user wants to book a new medical appointment for an existing patient. "
        "Requires: patient_name, doctor_id (from hospital_list_doctors), "
        "appointment_date (YYYY-MM-DD), appointment_time (HH:MM), and reason for visit. "
        "Do NOT use this tool if the patient is not yet registered — use hospital_register_patient first. "
        "Do NOT use this tool to cancel or reschedule — use hospital_cancel_appointment instead. "
        "Returns appointment_id and full booking details."
    )
)
def hospital_book_appointment(
    patient_name: str,
    doctor_id: str,
    appointment_date: str,
    appointment_time: str,
    reason: str,
) -> str:
    missing = [f for f, v in [
        ("patient_name", patient_name), ("doctor_id", doctor_id),
        ("appointment_date", appointment_date), ("appointment_time", appointment_time),
        ("reason", reason),
    ] if not v or not str(v).strip()]
    if missing:
        return _err(f"Missing required fields: {', '.join(missing)}")

    try:
        appt_date = datetime.strptime(appointment_date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return _err("appointment_date must be in YYYY-MM-DD format.")

    if appt_date < date.today():
        return _err("appointment_date cannot be in the past.")

    try:
        datetime.strptime(appointment_time.strip(), "%H:%M")
    except ValueError:
        return _err("appointment_time must be in HH:MM format.")

    patient_row = hospital_db.get_patient_by_name(patient_name)
    if not patient_row:
        return _err(f"Patient '{patient_name}' not found. Please register first.")
    patient_id, pat_name = patient_row

    doctor_row = hospital_db.get_doctor(doctor_id)
    if not doctor_row:
        return _err(f"Doctor '{doctor_id}' not found.")
    doc_id, doc_name, specialty, _, avail_days, _, fee = doctor_row

    weekday = appt_date.strftime("%a")
    if weekday not in avail_days:
        return _err(
            f"{doc_name} is not available on {weekday}. Working days: {avail_days}."
        )

    if hospital_db.check_appointment_conflict(doc_id, appointment_date.strip(), appointment_time.strip()):
        return _err(
            f"{doc_name} already has a booking at {appointment_date} {appointment_time}. Please choose another time."
        )

    appointment_id = hospital_db.create_appointment(
        patient_id, doc_id, appointment_date.strip(), appointment_time.strip(), reason
    )

    return _ok({
        "appointment_id": appointment_id,
        "status": "scheduled",
        "patient_id": patient_id,
        "patient_name": pat_name,
        "doctor_id": doc_id,
        "doctor_name": doc_name,
        "specialty": specialty,
        "date": appointment_date.strip(),
        "time": appointment_time.strip(),
        "reason": reason.strip(),
        "consultation_fee": fee,
        "note": "Please arrive 15 minutes early and bring your ID card.",
    })


@mcp_hospital.tool(
    name="hospital_cancel_appointment",
    description=(
        "Use this tool when the user wants to cancel an existing scheduled appointment. "
        "Requires appointment_id (from hospital_book_appointment or hospital_get_patient_appointments). "
        "Do NOT use this tool on completed appointments — those cannot be cancelled. "
        "Do NOT use this tool to book a new appointment — use hospital_book_appointment instead. "
        "Returns the updated appointment status and details."
    )
)
def hospital_cancel_appointment(appointment_id: str, reason: str = "") -> str:
    appt_id = appointment_id.strip().upper()
    row = hospital_db.get_appointment(appt_id)
    if not row:
        return _err(f"Appointment '{appt_id}' not found.")

    aid, status, appt_date, appt_time, doc_name, pat_name = row

    if status == "cancelled":
        return _err(f"Appointment '{appt_id}' is already cancelled.")
    if status == "completed":
        return _err("Cannot cancel a completed appointment.")

    notes = f"Cancelled by patient. Reason: {reason}" if reason else "Cancelled by patient."
    hospital_db.cancel_appointment(appt_id, notes)

    return _ok({
        "appointment_id": appt_id,
        "status": "cancelled",
        "patient_name": pat_name,
        "doctor_name": doc_name,
        "date": appt_date,
        "time": appt_time,
        "cancellation_notes": notes,
    })


@mcp_hospital.tool(
    name="hospital_get_patient_appointments",
    description=(
        "Use this tool when the user wants to view all appointments for a patient, "
        "optionally filtered by status (scheduled / completed / cancelled / all). "
        "Do NOT use this tool to book or cancel appointments — "
        "use hospital_book_appointment or hospital_cancel_appointment instead. "
        "Do NOT use this tool to look up patient profile details — use hospital_get_patient_info. "
        "Returns a list of appointments, each with appointment_id for use in cancel or follow-up tools."
    )
)
def hospital_get_patient_appointments(patient_name: str, status_filter: str = "all") -> str:
    patient_row = hospital_db.get_patient_by_name(patient_name)
    if not patient_row:
        return _err(f"Patient '{patient_name}' not found.")

    patient_id, pat_name = patient_row
    rows = hospital_db.get_patient_appointments(patient_id, status_filter.strip().lower())

    return _ok({
        "patient_id": patient_id,
        "patient_name": pat_name,
        "status_filter": status_filter,
        "total": len(rows),
        "appointments": [
            {
                "appointment_id": aid,
                "doctor_name": doc_name,
                "specialty": specialty,
                "date": appt_date,
                "time": appt_time,
                "status": status,
                "reason": reason,
                "notes": notes,
            }
            for aid, doc_name, specialty, appt_date, appt_time, status, reason, notes in rows
        ],
    })


@mcp_hospital.tool(
    name="hospital_register_patient",
    description=(
        "Use this tool when the user wants to register a new patient who does not yet exist in the system. "
        "Requires: name, date_of_birth (YYYY-MM-DD), gender (Male/Female), phone, id_number (national ID). "
        "Do NOT use this tool if the patient is already registered — use hospital_get_patient_info to verify first. "
        "Do NOT use this tool to update existing patient records. "
        "Returns patient_id which is needed for booking appointments."
    )
)
def hospital_register_patient(
    name: str,
    date_of_birth: str,
    gender: str,
    phone: str,
    id_number: str,
) -> str:
    missing = [f for f, v in [
        ("name", name), ("date_of_birth", date_of_birth),
        ("gender", gender), ("phone", phone), ("id_number", id_number),
    ] if not v or not str(v).strip()]
    if missing:
        return _err(f"Missing required fields: {', '.join(missing)}")

    try:
        datetime.strptime(date_of_birth.strip(), "%Y-%m-%d")
    except ValueError:
        return _err("date_of_birth must be in YYYY-MM-DD format.")

    gender = gender.strip().capitalize()
    if gender not in ("Male", "Female"):
        return _err("gender must be 'Male' or 'Female'.")

    existing = hospital_db.patient_exists(name, id_number)
    if existing:
        return _err(f"Patient already registered with patient_id: {existing[0]}")

    patient_id = hospital_db.create_patient(name, date_of_birth, gender, phone, id_number)

    return _ok({
        "patient_id": patient_id,
        "name": name.strip(),
        "date_of_birth": date_of_birth.strip(),
        "gender": gender,
        "phone": _mask_phone(phone),
        "status": "registered",
    })
