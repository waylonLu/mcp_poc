import sqlite3
import uuid
from datetime import datetime, date, timedelta


class HospitalDatabase:
    def __init__(self, db_path="db/hospital.sqlite3"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        print("Initialising hospital database...")
        with self.get_connection() as conn:
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
                self._insert_sample_data(conn)
            conn.commit()

    def _insert_sample_data(self, conn):
        print("Inserting hospital sample data...")
        doctors = [
            ("D001", "Dr. Chen Wei",   "Cardiology",        "Chief Physician",     "City Central Hospital", "Mon,Tue,Thu,Fri",     "09:00-12:00,14:00-17:00", 200.0),
            ("D002", "Dr. Liu Mei",    "Neurology",         "Associate Physician", "City Central Hospital", "Mon,Wed,Fri",         "08:30-11:30,13:30-16:30", 180.0),
            ("D003", "Dr. Zhang Hao",  "Orthopedics",       "Chief Physician",     "City Central Hospital", "Tue,Wed,Thu",         "09:00-12:00,14:00-17:00", 220.0),
            ("D004", "Dr. Wang Fang",  "Pediatrics",        "Attending Physician", "City Central Hospital", "Mon,Tue,Wed,Thu,Fri", "08:00-12:00",             150.0),
            ("D005", "Dr. Li Jian",    "General Surgery",   "Associate Physician", "City Central Hospital", "Mon,Wed,Fri",         "10:00-12:00,15:00-17:00", 160.0),
            ("D006", "Dr. Zhao Xin",   "Dermatology",       "Attending Physician", "City Central Hospital", "Tue,Thu,Fri",         "09:00-12:00",             120.0),
            ("D007", "Dr. Sun Ying",   "Ophthalmology",     "Chief Physician",     "City Central Hospital", "Mon,Tue,Thu",         "09:00-11:30,14:00-16:30", 180.0),
            ("D008", "Dr. Zhou Qiang", "Internal Medicine", "Associate Physician", "City Central Hospital", "Mon,Tue,Wed,Thu,Fri", "08:00-12:00,14:00-17:00", 130.0),
        ]
        conn.executemany("INSERT INTO doctors VALUES (?,?,?,?,?,?,?,?)", doctors)

        patients = [
            ("P001", "Alice Wong",  "1985-03-12", "Female", "138-0001-0001", "110101198503120011"),
            ("P002", "Bob Zhang",   "1992-07-25", "Male",   "139-0002-0002", "110101199207250021"),
            ("P003", "Carol Liu",   "1978-11-08", "Female", "137-0003-0003", "110101197811080031"),
            ("P004", "David Chen",  "2005-01-30", "Male",   "136-0004-0004", "110101200501300041"),
            ("P005", "Emily Wang",  "1965-05-20", "Female", "135-0005-0005", "110101196505200051"),
        ]
        conn.executemany("INSERT INTO patients VALUES (?,?,?,?,?,?)", patients)

        today = date.today()
        appointments = [
            (str(uuid.uuid4()), "P001", "D001", str(today + timedelta(days=2)), "10:00", "scheduled", "Chest pain check-up",        datetime.now().isoformat(), None),
            (str(uuid.uuid4()), "P002", "D003", str(today + timedelta(days=3)), "14:00", "scheduled", "Knee pain evaluation",        datetime.now().isoformat(), None),
            (str(uuid.uuid4()), "P003", "D008", str(today - timedelta(days=5)), "09:00", "completed", "Annual physical examination",  datetime.now().isoformat(), "All results normal"),
            (str(uuid.uuid4()), "P004", "D004", str(today + timedelta(days=1)), "08:30", "scheduled", "Vaccination follow-up",       datetime.now().isoformat(), None),
            (str(uuid.uuid4()), "P005", "D002", str(today - timedelta(days=2)), "14:30", "cancelled", "Headache consultation",        datetime.now().isoformat(), "Patient rescheduled"),
            (str(uuid.uuid4()), "P001", "D008", str(today + timedelta(days=7)), "09:30", "scheduled", "Blood test review",           datetime.now().isoformat(), None),
        ]
        conn.executemany("INSERT INTO appointments VALUES (?,?,?,?,?,?,?,?,?)", appointments)

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_specialties(self):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT specialty, COUNT(*) FROM doctors GROUP BY specialty ORDER BY specialty"
            ).fetchall()

    def get_doctors(self, specialty: str = ""):
        with self.get_connection() as conn:
            if specialty.strip():
                return conn.execute(
                    "SELECT id, name, specialty, title, hospital, available_days, available_times, consultation_fee "
                    "FROM doctors WHERE LOWER(specialty) = LOWER(?) ORDER BY name",
                    (specialty.strip(),)
                ).fetchall()
            return conn.execute(
                "SELECT id, name, specialty, title, hospital, available_days, available_times, consultation_fee "
                "FROM doctors ORDER BY specialty, name"
            ).fetchall()

    def get_doctor(self, doctor_id: str):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT id, name, specialty, title, available_days, available_times, consultation_fee "
                "FROM doctors WHERE id = ?",
                (doctor_id.strip(),)
            ).fetchone()

    def get_doctor_bookings(self, doctor_id: str):
        today = date.today()
        next_week = str(today + timedelta(days=7))
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT appointment_date, appointment_time, status FROM appointments "
                "WHERE doctor_id = ? AND appointment_date >= ? AND appointment_date <= ? AND status != 'cancelled' "
                "ORDER BY appointment_date, appointment_time",
                (doctor_id, str(today), next_week)
            ).fetchall()

    def get_patient(self, query: str):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT id, name, date_of_birth, gender, phone, id_number "
                "FROM patients WHERE id = ? OR LOWER(name) = LOWER(?)",
                (query, query)
            ).fetchone()

    def get_patient_by_name(self, name: str):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT id, name FROM patients WHERE LOWER(name) = LOWER(?)",
                (name.strip(),)
            ).fetchone()

    def check_appointment_conflict(self, doctor_id: str, appt_date: str, appt_time: str):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT id FROM appointments WHERE doctor_id = ? AND appointment_date = ? "
                "AND appointment_time = ? AND status != 'cancelled'",
                (doctor_id, appt_date, appt_time)
            ).fetchone()

    def create_appointment(self, patient_id: str, doctor_id: str, appt_date: str,
                           appt_time: str, reason: str) -> str:
        appt_id = str(uuid.uuid4())[:8].upper()
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO appointments (id, patient_id, doctor_id, appointment_date, appointment_time, "
                "status, reason, created_at, notes) VALUES (?,?,?,?,?,?,?,?,?)",
                (appt_id, patient_id, doctor_id, appt_date, appt_time,
                 "scheduled", reason.strip(), datetime.now().isoformat(), None)
            )
            conn.commit()
        return appt_id

    def get_appointment(self, appt_id: str):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT a.id, a.status, a.appointment_date, a.appointment_time, d.name, p.name "
                "FROM appointments a "
                "JOIN doctors d ON a.doctor_id = d.id "
                "JOIN patients p ON a.patient_id = p.id "
                "WHERE a.id = ?",
                (appt_id,)
            ).fetchone()

    def cancel_appointment(self, appt_id: str, notes: str):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE appointments SET status = 'cancelled', notes = ? WHERE id = ?",
                (notes, appt_id)
            )
            conn.commit()

    def get_patient_appointments(self, patient_id: str, status_filter: str = "all"):
        with self.get_connection() as conn:
            sql = (
                "SELECT a.id, d.name, d.specialty, a.appointment_date, a.appointment_time, "
                "a.status, a.reason, a.notes "
                "FROM appointments a JOIN doctors d ON a.doctor_id = d.id "
                "WHERE a.patient_id = ? "
            )
            if status_filter != "all":
                return conn.execute(
                    sql + "AND a.status = ? ORDER BY a.appointment_date DESC, a.appointment_time DESC",
                    (patient_id, status_filter)
                ).fetchall()
            return conn.execute(
                sql + "ORDER BY a.appointment_date DESC, a.appointment_time DESC",
                (patient_id,)
            ).fetchall()

    def patient_exists(self, name: str, id_number: str):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT id FROM patients WHERE LOWER(name) = LOWER(?) AND id_number = ?",
                (name.strip(), id_number.strip())
            ).fetchone()

    def create_patient(self, name: str, dob: str, gender: str, phone: str, id_number: str) -> str:
        patient_id = f"P{str(uuid.uuid4())[:6].upper()}"
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO patients (id, name, date_of_birth, gender, phone, id_number) VALUES (?,?,?,?,?,?)",
                (patient_id, name.strip(), dob.strip(), gender, phone.strip(), id_number.strip())
            )
            conn.commit()
        return patient_id


hospital_db = HospitalDatabase()
