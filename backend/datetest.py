from datetime import date

# Your function
def get_weekday_number(booking_date: date) -> int:
    """
    Returns weekday number based on Python standard:
    Monday = 0 ... Sunday = 6
    """
    return booking_date.weekday()

# -----------------------------
# Test cases
# -----------------------------

# 1. Test 25 Dec 2025 → Thursday (3)
d1 = date(2025, 12, 28)
print(d1, "→", get_weekday_number(d1))  # Expected: 3


