# -----------------------------
# TEST CAPACITY & WINDOWS
# -----------------------------

import sqlite3
from datetime import datetime, timedelta
import uuid
DB_PATH = "lab_system.db"



def get_daily_capacity(test_id, schedule_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT duration FROM tests WHERE test_id=?", (test_id,))
        row = cursor.fetchone()
        duration = int(row[0]) if row and row[0] else 1

        cursor.execute("SELECT opens_at, closes_at FROM test_schedule WHERE schedule_id=?", (schedule_id,))
        row = cursor.fetchone()
        if not row or not row[0] or not row[1]:
            return 1
        opens_at, closes_at = row

    fmt = "%H:%M"
    start = datetime.strptime(opens_at, fmt)
    end = datetime.strptime(closes_at, fmt)
    working_minutes = int((end - start).total_seconds() / 60)
    if working_minutes <= 0:
        return 1

    max_raw = working_minutes // duration
    realistic = max(int(max_raw * 0.75), 1)
    return realistic

def generate_windows_for_schedule(test_id, schedule_id, window_minutes: int):
    fmt = "%H:%M"
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT opens_at, closes_at FROM test_schedule WHERE schedule_id=?", (schedule_id,))
        row = cursor.fetchone()
        if not row or not row[0] or not row[1]:
            return
        opens_at, closes_at = row

        start_time = datetime.strptime(opens_at, fmt)
        end_time = datetime.strptime(closes_at, fmt)
        working_minutes = int((end_time - start_time).total_seconds() / 60)
        if working_minutes <= 0 or window_minutes <= 0:
            return

        # generate windows
        windows = []
        current_start = start_time
        window_index = 0
        while current_start < end_time:
            current_end = current_start + timedelta(minutes=window_minutes)
            if current_end > end_time:
                current_end = end_time
            windows.append((window_index, current_start.strftime(fmt), current_end.strftime(fmt)))
            window_index += 1
            current_start = current_end

        if not windows:
            return

        # calculate capacity
        total_capacity = get_daily_capacity(test_id, schedule_id)
        win_count = len(windows)
        base = total_capacity // win_count
        extra = total_capacity % win_count
        capacities = [base + (1 if i < extra else 0) for i in range(win_count)]

        # delete existing windows for schedule
        cursor.execute("DELETE FROM test_schedule_windows WHERE schedule_id=?", (schedule_id,))

        # insert new windows
        for idx, (win_index, win_start, win_end) in enumerate(windows):
            window_id = str(uuid.uuid4())
            max_tests = capacities[idx]
            cursor.execute("""
                INSERT INTO test_schedule_windows
                (window_id, test_id, schedule_id, window_index, window_start, window_end, max_tests)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (window_id, test_id, schedule_id, win_index, win_start, win_end, max_tests))

        conn.commit()





# import sqlite3
# from datetime import datetime, timedelta
# import uuid

# DB_PATH = "lab_system.db"

# def get_daily_capacity(test_id, schedule_id):
#     """
#     Calculate daily capacity for a test for a given schedule.
#     """
#     with sqlite3.connect(DB_PATH) as conn:
#         cursor = conn.cursor()

#         # Get duration of test
#         cursor.execute("SELECT duration FROM tests WHERE test_id=?", (test_id,))
#         row = cursor.fetchone()
#         duration = int(row[0]) if row and row[0] else 1  # ensure integer

#         # Get schedule opens/closes
#         cursor.execute("SELECT opens_at, closes_at FROM test_schedule WHERE schedule_id=?", (schedule_id,))
#         row = cursor.fetchone()
#         if not row or not row[0] or not row[1]:
#             return 1  # default 1 slot if not set
#         opens_at, closes_at = row

#     fmt = "%H:%M"
#     start = datetime.strptime(opens_at, fmt)
#     end = datetime.strptime(closes_at, fmt)
#     working_minutes = int((end - start).total_seconds() / 60)

#     if working_minutes <= 0:
#         return 1  # fallback if timing invalid

#     max_raw = working_minutes // duration
#     realistic = max(int(max_raw * 0.75), 1)  # apply burnout factor, at least 1
#     return realistic

# def generate_windows_and_capacity(test_id, window_minutes=120):
#     """
#     Generate windows for all schedules of a test_id
#     and calculate max_tests per window.
#     Insert into test_schedule_windows.
#     """
#     fmt = "%H:%M"

#     with sqlite3.connect(DB_PATH) as conn:
#         cursor = conn.cursor()
#         cursor.execute("PRAGMA foreign_keys = ON;")

#         # Check if test_id exists in test_schedule
#         cursor.execute("SELECT COUNT(*) FROM test_schedule WHERE test_id=?", (test_id,))
#         count = cursor.fetchone()[0]
#         if count == 0:
#             print(f"❌ Error: test_id '{test_id}' does not exist in test_schedule table.")
#             return  # stop execution

#         # Get all schedules for this test
#         cursor.execute("""
#             SELECT schedule_id, opens_at, closes_at
#             FROM test_schedule
#             WHERE test_id=?
#         """, (test_id,))
#         schedules = cursor.fetchall()

#         for schedule in schedules:
#             schedule_id, opens_at, closes_at = schedule

#             if not opens_at or not closes_at:
#                 print(f"⚠️ Schedule {schedule_id} missing timing, skipping")
#                 continue

#             start_time = datetime.strptime(opens_at, fmt)
#             end_time = datetime.strptime(closes_at, fmt)
#             working_minutes = int((end_time - start_time).total_seconds() / 60)

#             if working_minutes <= 0 or window_minutes <= 0:
#                 print(f"⚠️ Invalid timings or window size for schedule {schedule_id}, skipping")
#                 continue

#             # Generate windows
#             windows = []
#             current_start = start_time
#             window_index = 0
#             while current_start < end_time:
#                 current_end = current_start + timedelta(minutes=window_minutes)
#                 if current_end > end_time:
#                     current_end = end_time
#                 windows.append((window_index, current_start.strftime(fmt), current_end.strftime(fmt)))
#                 window_index += 1
#                 current_start = current_end

#             win_count = len(windows)
#             if win_count == 0:
#                 print(f"⚠️ No windows generated for schedule {schedule_id}, skipping")
#                 continue

#             # Calculate daily capacity for this schedule
#             total_capacity = get_daily_capacity(test_id, schedule_id)

#             # Distribute capacity into windows
#             base = total_capacity // win_count
#             extra = total_capacity % win_count
#             capacities = []
#             for i in range(win_count):
#                 add = 1 if i < extra else 0
#                 capacities.append(base + add)

#             # Insert into test_schedule_windows
#             for idx, (win_index, win_start, win_end) in enumerate(windows):
#                 window_id = str(uuid.uuid4())
#                 max_tests = capacities[idx]
#                 cursor.execute("""
#                     INSERT OR REPLACE INTO test_schedule_windows
#                     (window_id, test_id, schedule_id, window_index, window_start, window_end, max_tests)
#                     VALUES (?, ?, ?, ?, ?, ?, ?)
#                 """, (window_id, test_id, schedule_id, win_index, win_start, win_end, max_tests))

#         conn.commit()

#     print(f"✅ Windows and capacities generated for test_id: {test_id}")

# # -----------------------------
# # Example usage
# # -----------------------------
# if __name__ == "__main__":
#     test_id = "f7d14a4d-4fec-45c4-af86-051f8754781f"  # replace with actual test_id from your DB
#     window_minutes = 120            # change window size as needed
#     generate_windows_and_capacity(test_id, window_minutes)
