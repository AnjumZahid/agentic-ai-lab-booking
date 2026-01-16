import sqlite3
import uuid

# ===========================
# DATABASE
# ===========================
DB_PATH = "lab_system.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lab_schedule (
            schedule_id TEXT PRIMARY KEY,
            day_of_week INTEGER,
            opens_at TEXT,
            closes_at TEXT,
            is_closed INTEGER
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM lab_schedule")
    count = cursor.fetchone()[0]

    # Insert default schedule only if empty
    if count == 0:
        default_data = []
        for day in range(7):
            if day < 5:  
                # Monday–Friday (0-4)
                default_data.append((
                    str(uuid.uuid4()), day, "08:00", "16:00", 0
                ))
            else:
                # Saturday–Sunday (5-6)
                default_data.append((
                    str(uuid.uuid4()), day, "00:00", "00:00", 1
                ))

        cursor.executemany("""
            INSERT INTO lab_schedule (schedule_id, day_of_week, opens_at, closes_at, is_closed)
            VALUES (?, ?, ?, ?, ?)
        """, default_data)

     # ------------------------
    # Lab Holidays Table
    # ------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lab_holidays (
            holiday_id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            opens_at TEXT,
            closes_at TEXT,
            is_closed BOOLEAN NOT NULL,
            remarks TEXT
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tests (
        test_id TEXT PRIMARY KEY,
        test_name TEXT NOT NULL,
        category TEXT DEFAULT 'normal' CHECK(category IN ('normal', 'special')),
        requires_booking INTEGER DEFAULT 0,
        requires_doctor INTEGER DEFAULT 0,
        price REAL DEFAULT 0,
        duration TEXT DEFAULT '00:30'  -- store duration as string "HH:MM" or as minutes integer
    )
""")

    # ------------------------
    # Test Schedule Table
    # ------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_schedule (
            schedule_id TEXT PRIMARY KEY,
            test_id TEXT NOT NULL,
            day_of_week INTEGER NOT NULL,
            opens_at TEXT,
            closes_at TEXT,
            is_closed INTEGER DEFAULT 0,
            FOREIGN KEY (test_id) REFERENCES tests(test_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_schedule_windows (
        window_id TEXT PRIMARY KEY,
        schedule_id TEXT NOT NULL,
        test_id TEXT NOT NULL,  -- new column added
        window_index INTEGER NOT NULL,

        window_start TEXT NOT NULL,
        window_end TEXT NOT NULL,

        max_tests INTEGER NOT NULL,

        FOREIGN KEY (schedule_id)
            REFERENCES test_schedule(schedule_id)
            ON DELETE CASCADE,

        FOREIGN KEY (test_id)
            REFERENCES tests(test_id)
            ON DELETE CASCADE,

        UNIQUE (schedule_id, window_index)
    )
""")


    # ------------------------
    # Doctors Table
    # ------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id TEXT PRIMARY KEY,
            doctor_name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            contact_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ------------------------
    # Doctor Holidays Table
    # ------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_holidays (
            doctor_holiday_id TEXT PRIMARY KEY,
            doctor_id TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            date TEXT NOT NULL,
            opens_at TEXT,
            closes_at TEXT,
            is_closed BOOLEAN NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
                ON DELETE CASCADE
        )
    """)

    # ---------- test_holidays ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_holidays (
            test_holiday_id TEXT PRIMARY KEY,
            test_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            date TEXT NOT NULL,
            opens_at TEXT,
            closes_at TEXT,
            is_closed INTEGER NOT NULL,
            FOREIGN KEY (test_id) REFERENCES tests(test_id) ON DELETE CASCADE
        )
        """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_doctor_assignments (
            assignment_id TEXT PRIMARY KEY,
            test_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            FOREIGN KEY(test_id) REFERENCES tests(test_id) ON DELETE CASCADE,
            FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            window_id TEXT NOT NULL,    
            test_id TEXT NOT NULL,
            doctor_id TEXT,
            patient_name TEXT NOT NULL,
            patient_mobile TEXT,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            window_start TEXT NOT NULL,
            window_end TEXT NOT NULL,
            doctor_name TEXT,
            FOREIGN KEY(test_id) REFERENCES tests(test_id) ON DELETE CASCADE,
            FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id)
        );
        """)


    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_test_doctor_unique
        ON test_doctor_assignments (doctor_id, test_id)
    """)

    conn.commit()
    conn.close()