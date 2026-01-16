from fastapi import FastAPI, HTTPException, Depends, Header, Query
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import uuid
from datetime import date, time
from contextlib import asynccontextmanager
from utils.schedule_win import generate_windows_for_schedule

from datetime import datetime, timedelta
from backend.db_table import init_db, DB_PATH

def time_str_to_minutes(t: str):
    """Convert 'HH:MM' string to total minutes"""
    h, m = map(int, t.split(":"))
    return h * 60 + m

def lc(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().lower()
    return value


# ===========================
# Lifespan
# ===========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    init_db()
    yield
    # Shutdown code (if any)

# ===========================
# FastAPI app
# ===========================
app = FastAPI(title="Lab Management Backend", lifespan=lifespan)

# ------------------------------------------------
# SIMPLE ADMIN AUTH (stored in memory for now)
# ------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"
VALID_TOKENS = set()

def verify_admin_token(authorization: str = Header(None)):
    """Check if admin token is valid"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise Exception()
    except:
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    if token not in VALID_TOKENS:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    return True

# ------------------------------------------------
# LOGIN ENDPOINT
# ------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginRequest):
    global ADMIN_PASSWORD

    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD:
        token = str(uuid.uuid4())
        VALID_TOKENS.add(token)
        return {"status": "success", "token": token}

    raise HTTPException(status_code=401, detail="Invalid username or password")

# ------------------------------------------------
# RESET PASSWORD
# ------------------------------------------------
class PasswordResetRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

@app.post("/reset-password")
def reset_password(
    data: PasswordResetRequest,
    is_admin: bool = Depends(verify_admin_token)
):
    global ADMIN_PASSWORD

    if data.old_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")

    ADMIN_PASSWORD = data.new_password

    # Clear old tokens
    VALID_TOKENS.clear()

    return {"status": "success", "message": "Password updated successfully. Please login again."}



# ===========================
# ENDPOINTS
# ===========================

class LabSchedule(BaseModel):
    day_of_week: int
    opens_at: str
    closes_at: str
    is_closed: int


# Fetch all schedules

@app.get("/lab/schedule")
def get_all_schedules():
    day_map = {
        0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
        4: "Friday", 5: "Saturday", 6: "Sunday"
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM lab_schedule ORDER BY day_of_week")
    rows = cursor.fetchall()

    schedules = []
    for r in rows:
        day_name = day_map.get(r[1], str(r[1]))  # map 0-6 to day names
        schedules.append({
            "schedule_id": r[0],
            "day_of_week": day_name,
            "opens_at": r[2],
            "closes_at": r[3],
            "is_closed": bool(r[4])
        })

    conn.close()
    return schedules

# Update a single day schedule
@app.put("/lab/schedule/{schedule_id}")
def update_schedule(schedule_id: str, schedule: LabSchedule):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE lab_schedule
        SET day_of_week=?, opens_at=?, closes_at=?, is_closed=?
        WHERE schedule_id=?
    """, (
        schedule.day_of_week,
        lc(schedule.opens_at),
        lc(schedule.closes_at),
        schedule.is_closed,
        schedule_id
    ))

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Schedule not found")

    conn.close()
    return {"success": True, "message": "Schedule updated successfully"}



# ===========================
# ENDPOINTS Holidays
# ===========================

class Holiday(BaseModel):
    date: str           # format 'YYYY-MM-DD'
    opens_at: str       # e.g., '09:00'
    closes_at: str      # e.g., '13:00'
    is_closed: bool     # True if full holiday, False if half-day
    remarks: Optional[str] = ""  # <-- add this

@app.post("/lab/holidays")
def create_holiday(holiday: Holiday):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    holiday_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO lab_holidays (holiday_id, date, opens_at, closes_at, is_closed, remarks)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        holiday_id,
        holiday.date,
        lc(holiday.opens_at),
        lc(holiday.closes_at),
        holiday.is_closed,
        holiday.remarks
    ))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Holiday created successfully", "holiday_id": holiday_id}


@app.get("/lab/holidays")
def get_all_holidays():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM lab_holidays ORDER BY date")
    rows = cursor.fetchall()

    holidays = [
        {
            "holiday_id": r[0],
            "date": r[1],
            "opens_at": r[2],
            "closes_at": r[3],
            "is_closed": r[4],
            "remarks": r[5] if len(r) > 5 else ""
        } for r in rows
    ]

    conn.close()
    return holidays


@app.put("/lab/holidays/{holiday_id}")
def update_holiday(holiday_id: str, holiday: Holiday):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE lab_holidays
        SET date=?, opens_at=?, closes_at=?, is_closed=?, remarks=?
        WHERE holiday_id=?
    """, (
        holiday.date,
        lc(holiday.opens_at),
        lc(holiday.closes_at),
        holiday.is_closed,
        holiday.remarks,
        holiday_id
    ))

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Holiday not found")

    conn.close()
    return {"success": True, "message": "Holiday updated successfully"}


@app.delete("/lab/holidays/{holiday_id}")
def delete_holiday(holiday_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM lab_holidays WHERE holiday_id=?", (holiday_id,))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Holiday not found")

    conn.close()
    return {"success": True, "message": "Holiday deleted successfully"}

# ================================
# TESTS END POINT
# ================================

class Test(BaseModel):
    test_name: str
    category: str = "normal"  # normal / special
    requires_booking: int = 0
    requires_doctor: int = 0
    price: Optional[float] = None       # New field for test price
    duration: Optional[str] = None      # New field for test duration, e.g., '30 min'



@app.post("/lab/tests")
def create_test(test: Test):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    test_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO tests (test_id, test_name, category, requires_booking, requires_doctor, price, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        test_id,
        lc(test.test_name),
        lc(test.category),
        test.requires_booking,
        test.requires_doctor,
        test.price,
        test.duration
    ))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Test created successfully", "test_id": test_id}


@app.get("/lab/tests")
def get_all_tests():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tests ORDER BY test_name")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "test_id": r[0],
            "test_name": r[1],
            "category": r[2],
            "requires_booking": r[3],
            "requires_doctor": r[4],
            "price": r[5],
            "duration": r[6]
        } for r in rows
    ]


@app.put("/lab/tests/{test_id}")
def update_test(test_id: str, test: Test):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tests
        SET test_name=?, category=?, requires_booking=?, requires_doctor=?, price=?, duration=?
        WHERE test_id=?
    """, (
        lc(test.test_name),
        lc(test.category),
        test.requires_booking,
        test.requires_doctor,
        test.price,
        test.duration,
        test_id
    ))

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")

    conn.close()
    return {"success": True, "message": "Test updated successfully"}


@app.delete("/lab/tests/{test_id}")
def delete_test(test_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tests WHERE test_id=?", (test_id,))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")

    conn.close()
    return {"success": True, "message": "Test deleted successfully"}


# ================================
# TESTS SCHEDULE END POINT
# ================================

class TestSchedule(BaseModel):
    test_id: str
    day_of_week: int
    opens_at: str | None = None
    closes_at: str | None = None
    is_closed: int = 0


# -----------------------------
# DAY HELPERS
# -----------------------------
DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

def validate_day(day: int):
    if day < 0 or day > 6:
        raise HTTPException(status_code=400, detail="day_of_week must be between 0 (Monday) and 6 (Sunday)")

def day_name(day: int) -> str:
    return DAY_NAMES[day]

# ===========================
# CREATE TEST SCHEDULE
# ===========================
@app.post("/lab/test-schedule")
def create_test_schedule(schedule: TestSchedule, window_minutes: int):
    validate_day(schedule.day_of_week)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Validate test exists
    cursor.execute("SELECT test_id FROM tests WHERE test_id=?", (schedule.test_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")

    schedule_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO test_schedule (
            schedule_id, test_id, day_of_week, opens_at, closes_at, is_closed
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (schedule_id, schedule.test_id, schedule.day_of_week,
          schedule.opens_at, schedule.closes_at, schedule.is_closed))
    conn.commit()
    conn.close()

    generate_windows_for_schedule(schedule.test_id, schedule_id, window_minutes)

    return {
        "success": True,
        "message": "Test schedule created successfully",
        "schedule_id": schedule_id
    }

# ===========================
# UPDATE TEST SCHEDULE
# ===========================
@app.put("/lab/test-schedule/{schedule_id}")
def update_test_schedule(schedule_id: str, schedule: TestSchedule, window_minutes: int):
    validate_day(schedule.day_of_week)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE test_schedule
        SET day_of_week=?, opens_at=?, closes_at=?, is_closed=?
        WHERE schedule_id=?
    """, (schedule.day_of_week, schedule.opens_at,
          schedule.closes_at, schedule.is_closed, schedule_id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Test schedule not found")

    cursor.execute("SELECT test_id FROM test_schedule WHERE schedule_id=?", (schedule_id,))
    test_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    generate_windows_for_schedule(test_id, schedule_id, window_minutes)

    return {
        "success": True,
        "message": "Test schedule updated successfully"
    }

# ===========================
# DELETE TEST SCHEDULE
# ===========================
@app.delete("/lab/test-schedule/{schedule_id}")
def delete_test_schedule(schedule_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM test_schedule_windows WHERE schedule_id=?", (schedule_id,))
    cursor.execute("DELETE FROM test_schedule WHERE schedule_id=?", (schedule_id,))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Test schedule not found")

    conn.close()
    return {
        "success": True,
        "message": "Test schedule and associated windows deleted successfully"
    }


# ===========================
# GET SCHEDULES BY TEST
# ===========================
@app.get("/lab/test-schedule/{test_id}")
def get_test_schedule(test_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            schedule_id,
            test_id,
            day_of_week,
            opens_at,
            closes_at,
            is_closed
        FROM test_schedule
        WHERE test_id=?
        ORDER BY day_of_week
    """, (test_id,))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "schedule_id": r[0],
            "test_id": r[1],
            "day_of_week": r[2],
            "day_name": day_name(r[2]),
            "opens_at": r[3],
            "closes_at": r[4],
            "is_closed": r[5],
        }
        for r in rows
    ]

# ===========================
# GET ALL TEST SCHEDULES
# ===========================
@app.get("/lab/test-schedule")
def get_all_test_schedules():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            ts.schedule_id,
            ts.test_id,
            t.test_name,
            ts.day_of_week,
            ts.opens_at,
            ts.closes_at,
            ts.is_closed
        FROM test_schedule ts
        JOIN tests t ON ts.test_id = t.test_id
        ORDER BY t.test_name, ts.day_of_week
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "schedule_id": r[0],
            "test_id": r[1],
            "test_name": r[2],
            "day_of_week": r[3],
            "day_name": day_name(r[3]),
            "opens_at": r[4],
            "closes_at": r[5],
            "is_closed": r[6],
        }
        for r in rows
    ]


# ===========================
# GET WINDOWS FOR SPECIFIC TEST
# ===========================
from typing import List

class TestScheduleWindow(BaseModel):
    window_id: str
    schedule_id: str
    test_id: str
    window_index: int
    window_start: str
    window_end: str
    max_tests: int


@app.get("/lab/test-windows/{test_id}", response_model=List[TestScheduleWindow])
def get_test_windows(test_id: str):
    """
    Fetch all windows for a given test_id from test_schedule_windows table.
    Returns schedule_id, window_index, start/end times, max_tests, and test_name.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tw.window_id, tw.schedule_id, tw.test_id, tw.window_index, 
               tw.window_start, tw.window_end, tw.max_tests
        FROM test_schedule_windows AS tw
        WHERE tw.test_id = ?
        ORDER BY tw.schedule_id, tw.window_index
    """, (test_id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No windows found for test_id '{test_id}'")

    # Format for front end
    return [
        TestScheduleWindow(
            window_id=r[0],
            schedule_id=r[1],
            test_id=r[2],
            window_index=r[3],
            window_start=r[4],
            window_end=r[5],
            max_tests=r[6]
        )
        for r in rows
    ]



# ================================
# DOCTORS  END POINT
# ================================

# ---------------------------
# GET ALL DOCTORS 
# ---------------------------


@app.get("/lab/doctors", response_model=List[dict])
def get_all_doctors():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT doctor_id, doctor_name, specialization, contact_info FROM doctors")
    rows = cursor.fetchall()
    conn.close()
    return [
        {"doctor_id": r[0], "doctor_name": r[1], "specialization": r[2], "contact_info": r[3]}
        for r in rows
    ]


# ---------------------------
# CREATE DOCTOR
# ---------------------------

class Doctor(BaseModel):
    doctor_name: str
    specialization: str
    contact_info: str | None = None  # optional field

@app.post("/lab/doctors")
def create_doctor(data: Doctor):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    doctor_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO doctors (doctor_id, doctor_name, specialization, contact_info)
        VALUES (?, ?, ?, ?)
    """, (
        doctor_id,
        lc(data.doctor_name),
        lc(data.specialization),
        lc(data.contact_info)
    ))
    conn.commit()
    conn.close()
    return {"doctor_id": doctor_id}


# ---------------------------
# UPDATE DOCTOR
# ---------------------------
@app.put("/lab/doctors/{doctor_id}")
def update_doctor(doctor_id: str, data: Doctor):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE doctors
        SET doctor_name = ?, specialization = ?, contact_info = ?, updated_at = CURRENT_TIMESTAMP
        WHERE doctor_id = ?
    """, (
        lc(data.doctor_name),
        lc(data.specialization),
        lc(data.contact_info),
        doctor_id
    ))
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    if not updated:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"status": "success"}


# ---------------------------
# DELETE DOCTOR
# ---------------------------
@app.delete("/lab/doctors/{doctor_id}")
def delete_doctor(doctor_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctors WHERE doctor_id = ?", (doctor_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return {"status": "deleted"}


# ================================
# DOCTORS HOLIDAYS END POINT
# ================================

class DoctorHoliday(BaseModel):
    doctor_id: str
    doctor_name: str       # auto-filled from doctors table
    date: str             # format 'YYYY-MM-DD'
    opens_at: str | None = None
    closes_at: str | None = None
    is_closed: bool

# --- 1. Create a new doctor holiday / half-day ---
@app.post("/lab/doctor-holidays")
def create_doctor_holiday(holiday: DoctorHoliday):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT doctor_name FROM doctors WHERE doctor_id=?", (holiday.doctor_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor_name = result[0]

    doctor_holiday_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO doctor_holidays (doctor_holiday_id, doctor_id, doctor_name, date, opens_at, closes_at, is_closed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        doctor_holiday_id,
        holiday.doctor_id,
        lc(doctor_name),
        holiday.date,
        lc(holiday.opens_at),
        lc(holiday.closes_at),
        holiday.is_closed
    ))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Doctor holiday created successfully", "doctor_holiday_id": doctor_holiday_id}


# --- 2. Read / fetch all doctor holidays ---
@app.get("/lab/doctor-holidays")
def get_all_doctor_holidays():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctor_holidays ORDER BY date")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "doctor_holiday_id": r[0],
            "doctor_id": r[1],
            "doctor_name": r[2],
            "date": r[3],
            "opens_at": r[4],
            "closes_at": r[5],
            "is_closed": r[6]
        } for r in rows
    ]


# --- 3. Update a doctor holiday / half-day ---
@app.put("/lab/doctor-holidays/{doctor_holiday_id}")
def update_doctor_holiday(doctor_holiday_id: str, holiday: DoctorHoliday):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT doctor_name FROM doctors WHERE doctor_id=?", (holiday.doctor_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor_name = result[0]

    cursor.execute("""
        UPDATE doctor_holidays
        SET doctor_id=?, doctor_name=?, date=?, opens_at=?, closes_at=?, is_closed=?
        WHERE doctor_holiday_id=?
    """, (
        holiday.doctor_id,
        lc(doctor_name),
        holiday.date,
        lc(holiday.opens_at),
        lc(holiday.closes_at),
        holiday.is_closed,
        doctor_holiday_id
    ))

    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor holiday not found")

    conn.close()
    return {"success": True, "message": "Doctor holiday updated successfully"}


# --- 4. Delete a doctor holiday / half-day ---
@app.delete("/lab/doctor-holidays/{doctor_holiday_id}")
def delete_doctor_holiday(doctor_holiday_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctor_holidays WHERE doctor_holiday_id=?", (doctor_holiday_id,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Doctor holiday not found")
    conn.close()
    return {"success": True, "message": "Doctor holiday deleted successfully"}


# ================================
# TESTS HOLIDAYS  END POINT
# ================================


class TestHoliday(BaseModel):
    test_id: str
    test_name: str         # auto-filled from tests table
    date: str              # format 'YYYY-MM-DD'
    opens_at: str | None = None
    closes_at: str | None = None
    is_closed: bool




# --- 1. Create a new test holiday / half-day ---
@app.post("/lab/test-holidays")
def create_test_holiday(holiday: TestHoliday):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Auto-fill test_name from tests table
    cursor.execute("SELECT test_name FROM tests WHERE test_id=?", (holiday.test_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")
    test_name = lc(result[0])  # store lowercase

    test_holiday_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO test_holidays (test_holiday_id, test_id, test_name, date, opens_at, closes_at, is_closed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        test_holiday_id,
        holiday.test_id,
        test_name,
        holiday.date,
        holiday.opens_at,
        holiday.closes_at,
        holiday.is_closed
    ))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Test holiday created successfully", "test_holiday_id": test_holiday_id}


# --- 2. Read / fetch all test holidays ---
@app.get("/lab/test-holidays")
def get_all_test_holidays():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM test_holidays ORDER BY date")
    rows = cursor.fetchall()

    holidays = [
        {
            "test_holiday_id": r[0],
            "test_id": r[1],
            "test_name": r[2],
            "date": r[3],
            "opens_at": r[4],
            "closes_at": r[5],
            "is_closed": r[6]
        } for r in rows
    ]

    conn.close()
    return holidays


# --- 3. Update a test holiday / half-day ---
@app.put("/lab/test-holidays/{test_holiday_id}")
def update_test_holiday(test_holiday_id: str, holiday: TestHoliday):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Auto-fill test_name from tests table
    cursor.execute("SELECT test_name FROM tests WHERE test_id=?", (holiday.test_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Test not found")
    test_name = lc(result[0])  # store lowercase

    cursor.execute("""
        UPDATE test_holidays
        SET test_id=?, test_name=?, date=?, opens_at=?, closes_at=?, is_closed=?
        WHERE test_holiday_id=?
    """, (
        holiday.test_id,
        test_name,
        holiday.date,
        holiday.opens_at,
        holiday.closes_at,
        holiday.is_closed,
        test_holiday_id
    ))

    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Test holiday not found")

    conn.close()
    return {"success": True, "message": "Test holiday updated successfully"}


# --- 4. Delete a test holiday / half-day ---
@app.delete("/lab/test-holidays/{test_holiday_id}")
def delete_test_holiday(test_holiday_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM test_holidays WHERE test_holiday_id=?", (test_holiday_id,))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Test holiday not found")

    conn.close()
    return {"success": True, "message": "Test holiday deleted successfully"}


# --------------------------
# TEST-DOCTOR ASSIGNMENTS END POINT
# --------------------------


class TestDoctorAssignment(BaseModel):
    test_id: str
    doctor_id: str
    


# --- 1. Create a new test-doctor assignment ---
@app.post("/lab/test-doctor-assignments")
def create_test_doctor_assignment(assignment: TestDoctorAssignment):
    try:
        with sqlite3.connect(DB_PATH, timeout=5, check_same_thread=False) as conn:
            cursor = conn.cursor()

            # Fetch test_name
            cursor.execute("SELECT test_name FROM tests WHERE test_id=?", (assignment.test_id,))
            t = cursor.fetchone()
            if not t:
                raise HTTPException(404, "Test not found")
            test_name = lc(t[0])  # store lowercase

            # Fetch doctor_name
            cursor.execute("SELECT doctor_name FROM doctors WHERE doctor_id=?", (assignment.doctor_id,))
            d = cursor.fetchone()
            if not d:
                raise HTTPException(404, "Doctor not found")
            doctor_name = lc(d[0])  # store lowercase

            # Generate assignment_id
            assignment_id = str(uuid.uuid4())

            # Insert assignment (will fail if doctor_id + test_id already exists)
            cursor.execute("""
                INSERT INTO test_doctor_assignments
                (assignment_id, test_id, test_name, doctor_id, doctor_name)
                VALUES (?, ?, ?, ?, ?)
            """, (assignment_id, assignment.test_id, test_name, assignment.doctor_id, doctor_name))

            conn.commit()
            return {"success": True, "assignment_id": assignment_id}

    except sqlite3.IntegrityError:
        # Raised if UNIQUE constraint violated
        raise HTTPException(
            status_code=400,
            detail="This test is already assigned to this doctor"
        )
    except sqlite3.OperationalError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database busy, please try again: {str(e)}"
        )


# --- 2. Read all assignments ---
@app.get("/lab/test-doctor-assignments")
def get_all_test_doctor_assignments():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_doctor_assignments")
    rows = cursor.fetchall()
    assignments = [
        {
            "assignment_id": r[0],
            "test_id": r[1],
            "test_name": r[2],
            "doctor_id": r[3],
            "doctor_name": r[4]
        } for r in rows
    ]
    conn.close()
    return assignments


# --- 3. Delete an assignment ---
@app.delete("/lab/test-doctor-assignments/{assignment_id}")
def delete_test_doctor_assignment(assignment_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM test_doctor_assignments WHERE assignment_id=?", (assignment_id,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Assignment not found")
    conn.close()
    return {"success": True, "message": "Assignment deleted"}



# ================================
# BOOKINGS  END POINT
# ================================


def calculate_adjusted_max(window_start, window_end, holiday_start, holiday_end, max_tests):
    """
    Reduce max_tests proportionally when availability overlaps partially
    (lab/test/doctor available only for part of the window).
    """

    w_start = time_str_to_minutes(window_start)
    w_end = time_str_to_minutes(window_end)
    h_start = time_str_to_minutes(holiday_start)
    h_end = time_str_to_minutes(holiday_end)

    window_minutes = w_end - w_start
    if window_minutes <= 0:
        return 0

    # Available time inside the window
    available_start = max(w_start, h_start)
    available_end = min(w_end, h_end)

    if available_start >= available_end:
        return 0  # no availability at all

    available_minutes = available_end - available_start

    # Proportional reduction
    fraction = available_minutes / window_minutes
    adjusted = max_tests * fraction

    # Round down safely (never exceed max_tests)
    adjusted_max = max(0, int(adjusted))

    return adjusted_max


class Booking(BaseModel):
    booking_id: Optional[str] = None

    # --- REQUIRED CORE ---
    test_id: str
    window_id: str

    # --- OPTIONAL DISPLAY ---
    test_name: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None

    # --- PATIENT ---
    patient_name: str
    patient_mobile: str

    # --- DATE ---
    booking_date: date

    # --- BACKEND DERIVED (DO NOT TRUST CLIENT) ---
    booking_time: Optional[time] = None
    window_start: Optional[time] = None
    window_end: Optional[time] = None


@app.post("/lab/bookings")
def create_booking(booking: Booking):
    return create_booking_internal(booking)


def create_booking_internal(booking: Booking) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # -----------------------------
    # Validate test
    # -----------------------------
    cursor.execute(
        "SELECT test_name, requires_doctor FROM tests WHERE test_id=?",
        (booking.test_id,)
    )
    test = cursor.fetchone()
    if not test:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Sorry, the selected test is invalid or not found in our system."
        )

    test_name, requires_doctor = test

    booking_date_str = booking.booking_date.isoformat()
    day_number = booking.booking_date.weekday()  # Monday=0

    # -----------------------------
    # Validate test schedule for day
    # -----------------------------
    cursor.execute("""
        SELECT schedule_id, is_closed
        FROM test_schedule
        WHERE test_id=? AND day_of_week=?
    """, (booking.test_id, day_number))

    schedule_row = cursor.fetchone()
    if not schedule_row:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Test is not scheduled for the selected date."
        )

    schedule_id, is_closed = schedule_row
    if is_closed:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Test is closed on the selected date."
        )

    # -----------------------------
    # Fetch window (STRICT)
    # -----------------------------
    cursor.execute("""
        SELECT window_id, window_start, window_end, max_tests
        FROM test_schedule_windows
        WHERE window_id=? AND test_id=? AND schedule_id=?
    """, (booking.window_id, booking.test_id, schedule_id))

    window_row = cursor.fetchone()
    if not window_row:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Invalid or unavailable time window for the selected date."
        )

    window_id, window_start, window_end, max_tests_schedule = window_row
    adjusted_max = max_tests_schedule

    # -----------------------------
    # BACKEND-DERIVED TIMING (KEY FIX)
    # -----------------------------
    booking_time = window_start

    booking.window_start = window_start
    booking.window_end = window_end
    booking.booking_time = booking_time

    # -----------------------------
    # Lab Holiday
    # -----------------------------
    cursor.execute("""
        SELECT is_closed, opens_at, closes_at
        FROM lab_holidays
        WHERE date=?
    """, (booking_date_str,))
    row = cursor.fetchone()
    if row:
        is_closed, opens_at, closes_at = row
        if is_closed:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Lab is closed on the selected date."
            )
        adjusted_max = min(
            adjusted_max,
            calculate_adjusted_max(
                window_start, window_end,
                opens_at, closes_at,
                max_tests_schedule
            )
        )

    # -----------------------------
    # Test Holiday
    # -----------------------------
    cursor.execute("""
        SELECT is_closed, opens_at, closes_at
        FROM test_holidays
        WHERE test_id=? AND date=?
    """, (booking.test_id, booking_date_str))
    row = cursor.fetchone()
    if row:
        is_closed, opens_at, closes_at = row
        if is_closed:
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Test is unavailable on the selected date."
            )
        adjusted_max = min(
            adjusted_max,
            calculate_adjusted_max(
                window_start, window_end,
                opens_at, closes_at,
                max_tests_schedule
            )
        )

    # -----------------------------
    # Doctor resolution + holiday
    # -----------------------------
    doctor_name = None

    if requires_doctor:
        # Resolve doctor_id
        if not booking.doctor_id:
            cursor.execute("""
                SELECT doctor_id
                FROM test_doctor_assignments
                WHERE test_id=?
            """, (booking.test_id,))
            row = cursor.fetchone()
            if row:
                booking.doctor_id = row[0]

        # Resolve doctor_name (ALWAYS)
        if booking.doctor_id:
            cursor.execute("""
                SELECT doctor_name
                FROM doctors
                WHERE doctor_id=?
            """, (booking.doctor_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                raise HTTPException(status_code=400, detail="Doctor not found")
            doctor_name = row[0]

            # Doctor holiday
            cursor.execute("""
                SELECT is_closed, opens_at, closes_at
                FROM doctor_holidays
                WHERE doctor_id=? AND date=?
            """, (booking.doctor_id, booking_date_str))
            row = cursor.fetchone()
            if row:
                is_closed, opens_at, closes_at = row
                if is_closed:
                    conn.close()
                    raise HTTPException(
                        status_code=400,
                        detail="Doctor unavailable on the selected date."
                    )
                adjusted_max = min(
                    adjusted_max,
                    calculate_adjusted_max(
                        window_start, window_end,
                        opens_at, closes_at,
                        max_tests_schedule
                    )
                )

    # -----------------------------
    # Existing bookings
    # -----------------------------
    cursor.execute("""
        SELECT COUNT(*)
        FROM bookings
        WHERE window_id=? AND booking_date=?
    """, (window_id, booking_date_str))
    booked = cursor.fetchone()[0]

    if adjusted_max - booked <= 0:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="Sorry, all slots are fully booked for this time window."
        )

    # -----------------------------
    # Insert booking
    # -----------------------------
    booking_id = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO bookings (
            booking_id, window_id, test_id, doctor_id, doctor_name,
            patient_name, patient_mobile,
            booking_date, booking_time,
            window_start, window_end
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        booking_id,
        window_id,
        booking.test_id,
        booking.doctor_id,
        doctor_name,
        booking.patient_name,
        booking.patient_mobile,
        booking_date_str,
        booking_time, 
        window_start,
        window_end
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Booking created successfully",
        "booking_id": booking_id,
        "test_name": test_name,
        "doctor_name": doctor_name
    }

# # -----------------------------
# # NEW ENDPOINT: AVAILABLE SLOTS
# # -----------------------------

# from datetime import datetime

@app.get("/lab/available-slots/{test_id}/{booking_date}")
def get_available_slots(test_id: str, booking_date: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # -----------------------------
    # Parse date & weekday
    # -----------------------------
    try:
        booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
    except ValueError:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    day_number = booking_date_obj.weekday()  # Monday=0 ... Sunday=6

    # -----------------------------
    # Get test schedule for the day
    # -----------------------------
    cursor.execute("""
        SELECT schedule_id, is_closed
        FROM test_schedule
        WHERE test_id=? AND day_of_week=?
    """, (test_id, day_number))
    schedule = cursor.fetchone()

    if not schedule:
        conn.close()
        return []  # no schedule for this day

    schedule_id, is_closed = schedule

    if is_closed:
        conn.close()
        return []

    # -----------------------------
    # Fetch ONLY windows for this schedule
    # -----------------------------
    cursor.execute("""
        SELECT window_id, window_start, window_end, max_tests
        FROM test_schedule_windows
        WHERE test_id=? AND schedule_id=?
        ORDER BY window_start
    """, (test_id, schedule_id))
    windows = cursor.fetchall()

    if not windows:
        conn.close()
        return []

    # -----------------------------
    # Pre-fetch holidays (once)
    # -----------------------------
    cursor.execute("""
        SELECT is_closed, opens_at, closes_at
        FROM lab_holidays
        WHERE date=?
    """, (booking_date,))
    lab_holiday = cursor.fetchone()

    cursor.execute("""
        SELECT is_closed, opens_at, closes_at
        FROM test_holidays
        WHERE test_id=? AND date=?
    """, (test_id, booking_date))
    test_holiday = cursor.fetchone()

    cursor.execute("SELECT requires_doctor FROM tests WHERE test_id=?", (test_id,))
    requires_doctor = cursor.fetchone()[0]

    doctor_holiday = None
    if requires_doctor:
        cursor.execute("""
            SELECT doctor_id FROM test_doctor_assignments WHERE test_id=?
        """, (test_id,))
        row = cursor.fetchone()
        if row:
            doctor_id = row[0]
            cursor.execute("""
                SELECT is_closed, opens_at, closes_at
                FROM doctor_holidays
                WHERE doctor_id=? AND date=?
            """, (doctor_id, booking_date))
            doctor_holiday = cursor.fetchone()

    # -----------------------------
    # Calculate availability per window
    # -----------------------------
    available_slots_list = []

    for window_id, window_start, window_end, max_tests in windows:
        adjusted_max = max_tests

        # Lab holiday
        if lab_holiday:
            is_closed, opens_at, closes_at = lab_holiday
            if is_closed:
                continue
            adjusted_max = min(
                adjusted_max,
                calculate_adjusted_max(
                    window_start, window_end,
                    opens_at, closes_at,
                    max_tests
                )
            )

        # Test holiday
        if test_holiday:
            is_closed, opens_at, closes_at = test_holiday
            if is_closed:
                continue
            adjusted_max = min(
                adjusted_max,
                calculate_adjusted_max(
                    window_start, window_end,
                    opens_at, closes_at,
                    max_tests
                )
            )

        # Doctor holiday
        if doctor_holiday:
            is_closed, opens_at, closes_at = doctor_holiday
            if is_closed:
                continue
            adjusted_max = min(
                adjusted_max,
                calculate_adjusted_max(
                    window_start, window_end,
                    opens_at, closes_at,
                    max_tests
                )
            )

        # Existing bookings
        cursor.execute("""
            SELECT COUNT(*)
            FROM bookings
            WHERE window_id=? AND booking_date=?
        """, (window_id, booking_date))
        booked = cursor.fetchone()[0]

        available = max(0, adjusted_max - booked)

        available_slots_list.append({
            "window_id": window_id,
            "window_start": window_start,
            "window_end": window_end,
            "available_slots": available
        })

    conn.close()
    return available_slots_list


# -----------------------------
# GET ALL BOOKINGS
# -----------------------------

@app.get("/lab/bookings")
def get_bookings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            b.booking_id,
            b.window_id,
            b.test_id,
            t.test_name,
            b.patient_name,
            b.patient_mobile,
            b.booking_date,
            b.booking_time,
            b.window_start,
            b.window_end,
            b.doctor_name
        FROM bookings b
        LEFT JOIN tests t ON t.test_id = b.test_id
        ORDER BY b.booking_date, b.booking_time
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "booking_id": r[0],
            "window_id": r[1],
            "test_id": r[2],
            "test_name": r[3] or "-",
            "patient_name": r[4] or "",
            "patient_mobile": r[5],
            "booking_date": r[6],
            "booking_time": r[7],
            "window_start": r[8],
            "window_end": r[9],
            "doctor_name": r[10] or "-"
        }
        for r in rows
    ]



# -----------------------------
# UPDATE BOOKING
# -----------------------------
@app.put("/lab/bookings/{booking_id}")
def update_booking(booking_id: str, booking: Booking):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # -----------------------------
    # Check if booking exists
    # -----------------------------
    cursor.execute("SELECT window_id, booking_date FROM bookings WHERE booking_id=?", (booking_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found")

    current_window_id, current_booking_date = existing

    # -----------------------------
    # Validate test
    # -----------------------------
    cursor.execute("SELECT test_name, requires_doctor FROM tests WHERE test_id=?", (booking.test_id,))
    test = cursor.fetchone()
    if not test:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid test")
    test_name, requires_doctor = test

    # -----------------------------
    # Validate window
    # -----------------------------
    cursor.execute("""
        SELECT window_id, window_start, window_end, max_tests
        FROM test_schedule_windows
        WHERE window_id=? AND test_id=?
    """, (booking.window_id, booking.test_id))
    window_row = cursor.fetchone()
    if not window_row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid window")
    window_id, window_start, window_end, max_tests_schedule = window_row

    booking_date_str = booking.booking_date.isoformat()
    adjusted_max = max_tests_schedule

    # -----------------------------
    # Lab holiday / half-day
    # -----------------------------
    cursor.execute("SELECT is_closed, opens_at, closes_at FROM lab_holidays WHERE date=?", (booking_date_str,))
    lab_holiday = cursor.fetchone()
    if lab_holiday:
        is_closed, opens_at, closes_at = lab_holiday
        if is_closed:
            conn.close()
            raise HTTPException(status_code=400, detail="Lab is closed on this date")
        adjusted_max = min(adjusted_max, calculate_adjusted_max(window_start, window_end, opens_at, closes_at, max_tests_schedule))

    # -----------------------------
    # Test holiday / half-day
    # -----------------------------
    cursor.execute("SELECT is_closed, opens_at, closes_at FROM test_holidays WHERE test_id=? AND date=?", (booking.test_id, booking_date_str))
    test_holiday = cursor.fetchone()
    if test_holiday:
        is_closed, opens_at, closes_at = test_holiday
        if is_closed:
            conn.close()
            raise HTTPException(status_code=400, detail="Test is unavailable on this date")
        adjusted_max = min(adjusted_max, calculate_adjusted_max(window_start, window_end, opens_at, closes_at, max_tests_schedule))

    # -----------------------------
    # Doctor assignment & holiday
    # -----------------------------
    doctor_name = None
    doctor_id = booking.doctor_id  # Use provided doctor_id if any

    if requires_doctor:
        # If doctor_id not provided, fetch from test_doctor_assignments
        if not doctor_id:
            cursor.execute("""
                SELECT doctor_id FROM test_doctor_assignments
                WHERE test_id=?
            """, (booking.test_id,))
            row = cursor.fetchone()
            doctor_id = row[0] if row else None

        if doctor_id:
            # Fetch doctor_name
            cursor.execute("SELECT doctor_name FROM doctors WHERE doctor_id=?", (doctor_id,))
            row = cursor.fetchone()
            doctor_name = row[0] if row else None

            # Doctor holiday check
            cursor.execute("SELECT is_closed, opens_at, closes_at FROM doctor_holidays WHERE doctor_id=? AND date=?", (doctor_id, booking_date_str))
            doc_holiday = cursor.fetchone()
            if doc_holiday:
                is_closed, opens_at, closes_at = doc_holiday
                if is_closed:
                    conn.close()
                    raise HTTPException(status_code=400, detail="Doctor is unavailable on this date")
                adjusted_max = min(adjusted_max, calculate_adjusted_max(window_start, window_end, opens_at, closes_at, max_tests_schedule))

    # -----------------------------
    # Existing bookings
    # -----------------------------
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE window_id=? AND booking_date=?", (booking.window_id, booking_date_str))
    booked = cursor.fetchone()[0]

    # Include current booking if window/date is unchanged
    if current_window_id == booking.window_id and current_booking_date == booking_date_str:
        booked -= 1

    if adjusted_max - booked <= 0:
        conn.close()
        raise HTTPException(status_code=400, detail="No available slots for the selected window/date")

    # -----------------------------
    # Update booking
    # -----------------------------
    cursor.execute("""
        UPDATE bookings
        SET test_id=?, window_id=?, doctor_id=?, doctor_name=?,
            patient_name=?, patient_mobile=?, booking_date=?, booking_time=?,
            window_start=?, window_end=?
        WHERE booking_id=?
    """, (
        booking.test_id,
        booking.window_id,
        doctor_id,
        doctor_name,
        booking.patient_name,
        booking.patient_mobile,
        booking_date_str,
        booking.booking_time.strftime("%H:%M"),
        window_start,
        window_end,
        booking_id
    ))

    conn.commit()
    conn.close()

    return {
        "message": "Booking updated successfully",
        "booking_id": booking_id,
        "test_name": test_name,
        "doctor_name": doctor_name
    }



# -----------------------------
# DELETE BOOKING
# -----------------------------
@app.delete("/lab/bookings/{booking_id}")
def delete_booking(booking_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT booking_id FROM bookings WHERE booking_id=?", (booking_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Booking not found")

    cursor.execute("DELETE FROM bookings WHERE booking_id=?", (booking_id,))
    conn.commit()
    conn.close()
    return {"message": "Booking deleted successfully"}


# if __name__ == "__main__":
#     from datetime import date

#     # -------------------------
#     # Manually set your test values
#     # -------------------------
#     test_id = "62eef921-0a4f-4974-b9df-2a1da34c7668"          # replace with actual test_id from DB
#     booking_date = "2026-01-01"            # YYYY-MM-DD

#     # -------------------------
#     # Call the function
#     # -------------------------
#     slots = get_available_slots(test_id, booking_date)

#     # -------------------------
#     # Print raw output
#     # -------------------------
#     # import pprint
#     # pprint.pprint(slots)
#     # print(slots)
#     import json
#     print(json.dumps(slots))


# if __name__ == "__main__":
#     # -----------------------------
#     # MANUAL BACKEND TEST
#     # -----------------------------

#     # 🔁 REPLACE THESE WITH REAL VALUES FROM YOUR DB
#     TEST_ID = "f7d14a4d-4fec-45c4-af86-051f8754781f"
#     BOOKING_DATE = "2025-12-26"  # YYYY-MM-DD

#     print("🔍 Testing get_available_slots()")
#     print(f"Test ID: {TEST_ID}")
#     print(f"Date   : {BOOKING_DATE}")
#     print("-" * 50)

#     slots = get_available_slots(TEST_ID, BOOKING_DATE)

#     if not slots:
#         print("❌ No windows found for this test.")
#     else:
#         for i, slot in enumerate(slots, start=1):
#             print(
#                 f"Slot {i}: "
#                 f"{slot['window_start']} - {slot['window_end']} | "
#                 f"Available: {slot['available_slots']} | "
#                 f"Window ID: {slot['window_id']}"
#             )

#     print("-" * 50)
#     print("✅ Test completed.")






















# # --- 1. Create booking ---
# @app.post("/lab/bookings")
# def create_booking(booking: Booking):
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     # -----------------------------
#     # Validate test exists
#     # -----------------------------
#     cursor.execute("SELECT test_name FROM tests WHERE test_id=?", (booking.test_id,))
#     test = cursor.fetchone()
#     if not test:
#         conn.close()
#         raise HTTPException(status_code=400, detail="Invalid test")
#     test_name = lc(test[0])  # store lowercase

#     # -----------------------------
#     # Validate doctor (if provided)
#     # -----------------------------
#     doctor_name = None
#     if booking.doctor_id:
#         cursor.execute("SELECT doctor_name FROM doctors WHERE doctor_id=?", (booking.doctor_id,))
#         doctor = cursor.fetchone()
#         if not doctor:
#             conn.close()
#             raise HTTPException(status_code=400, detail="Invalid doctor")
#         doctor_name = lc(doctor[0])  # store lowercase

#     # -----------------------------
#     # OVERLAP CHECK
#     # -----------------------------
#     cursor.execute("""
#         SELECT 1 FROM bookings
#         WHERE booking_date = ?
#           AND test_id = ?
#           AND (
#                 (? < window_end)
#             AND (? > window_start)
#           )
#     """, (
#         booking.booking_date.isoformat(),
#         booking.test_id,
#         booking.window_start.strftime("%H:%M"),
#         booking.window_end.strftime("%H:%M"),
#     ))

#     if cursor.fetchone():
#         conn.close()
#         raise HTTPException(status_code=400, detail="Booking time overlaps with an existing booking")

#     # -----------------------------
#     # INSERT
#     # -----------------------------
#     booking_id = str(uuid.uuid4())

#     cursor.execute("""
#         INSERT INTO bookings (
#             booking_id, test_id, doctor_id, doctor_name,
#             patient_name, patient_mobile,
#             booking_date, booking_time,
#             window_start, window_end
#         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """, (
#         booking_id,
#         booking.test_id,
#         booking.doctor_id,
#         doctor_name,
#         lc(booking.patient_name),   # store lowercase
#         lc(booking.patient_mobile), # store lowercase
#         booking.booking_date.isoformat(),
#         booking.booking_time.strftime("%H:%M"),
#         booking.window_start.strftime("%H:%M"),
#         booking.window_end.strftime("%H:%M"),
#     ))

#     conn.commit()
#     conn.close()

#     return {"message": "Booking created successfully", "booking_id": booking_id}


# # --- 2. List bookings ---
# @app.get("/lab/bookings")
# def list_bookings():
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute("""
#         SELECT
#             b.booking_id,
#             b.test_id,
#             t.test_name,
#             b.doctor_id,
#             d.doctor_name,
#             b.patient_name,
#             b.patient_mobile,
#             b.booking_date,
#             b.booking_time,
#             b.window_start,
#             b.window_end
#         FROM bookings b
#         JOIN tests t ON b.test_id = t.test_id
#         LEFT JOIN doctors d ON b.doctor_id = d.doctor_id
#         ORDER BY b.booking_date, b.booking_time
#     """)

#     rows = cursor.fetchall()
#     conn.close()

#     # Convert rows to dictionaries
#     bookings = []
#     for r in rows:
#         bookings.append({
#             "booking_id": r[0],
#             "test_id": r[1],
#             "test_name": lc(r[2]),
#             "doctor_id": r[3],
#             "doctor_name": lc(r[4]) if r[4] else None,
#             "patient_name": lc(r[5]),
#             "patient_mobile": lc(r[6]),
#             "booking_date": r[7],
#             "booking_time": r[8],
#             "window_start": r[9],
#             "window_end": r[10]
#         })
#     return bookings


# # --- 3. Update booking ---
# @app.put("/lab/bookings/{booking_id}")
# def update_booking(booking_id: str, booking: Booking):
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     # -----------------------------
#     # Check booking exists
#     # -----------------------------
#     cursor.execute("SELECT booking_id FROM bookings WHERE booking_id=?", (booking_id,))
#     if not cursor.fetchone():
#         conn.close()
#         raise HTTPException(status_code=404, detail="Booking not found")

#     # -----------------------------
#     # Validate test
#     # -----------------------------
#     cursor.execute("SELECT 1 FROM tests WHERE test_id=?", (booking.test_id,))
#     if not cursor.fetchone():
#         conn.close()
#         raise HTTPException(status_code=400, detail="Invalid test")

#     # -----------------------------
#     # Validate doctor (if provided)
#     # -----------------------------
#     if booking.doctor_id:
#         cursor.execute("SELECT 1 FROM doctors WHERE doctor_id=?", (booking.doctor_id,))
#         if not cursor.fetchone():
#             conn.close()
#             raise HTTPException(status_code=400, detail="Invalid doctor")

#     # -----------------------------
#     # OVERLAP CHECK (exclude self)
#     # -----------------------------
#     cursor.execute("""
#         SELECT 1 FROM bookings
#         WHERE booking_date = ?
#           AND test_id = ?
#           AND booking_id != ?
#           AND (
#                 (? < window_end)
#             AND (? > window_start)
#           )
#     """, (
#         booking.booking_date.isoformat(),
#         booking.test_id,
#         booking_id,
#         booking.window_start.strftime("%H:%M"),
#         booking.window_end.strftime("%H:%M"),
#     ))

#     if cursor.fetchone():
#         conn.close()
#         raise HTTPException(status_code=400, detail="Updated booking overlaps with another booking")

#     # -----------------------------
#     # UPDATE
#     # -----------------------------
#     cursor.execute("""
#         UPDATE bookings SET
#             test_id=?,
#             doctor_id=?,
#             patient_name=?,
#             patient_mobile=?,
#             booking_date=?,
#             booking_time=?,
#             window_start=?,
#             window_end=?
#         WHERE booking_id=?
#     """, (
#         booking.test_id,
#         booking.doctor_id,
#         lc(booking.patient_name),
#         lc(booking.patient_mobile),
#         booking.booking_date.isoformat(),
#         booking.booking_time.strftime("%H:%M"),
#         booking.window_start.strftime("%H:%M"),
#         booking.window_end.strftime("%H:%M"),
#         booking_id
#     ))

#     conn.commit()
#     conn.close()

#     return {"message": "Booking updated successfully"}


# # --- 4. Delete booking ---
# @app.delete("/lab/bookings/{booking_id}")
# def delete_booking(booking_id: str):
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     cursor.execute("DELETE FROM bookings WHERE booking_id=?", (booking_id,))
#     if cursor.rowcount == 0:
#         conn.close()
#         raise HTTPException(status_code=404, detail="Booking not found")

#     conn.commit()
#     conn.close()

#     return {"message": "Booking deleted successfully"}


# if __name__ == "__main__":
#     print(get_all_schedules())


# if __name__ == "__main__":
#     print(get_all_holidays())

