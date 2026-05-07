import holidays
import pandas as pd

def fetch_all():
    start = pd.Timestamp("2025-04-24")
    end   = pd.Timestamp.now()

    date_range = pd.date_range(start, end, freq="D")
    by_holidays = holidays.Germany(state="BY", years=range(start.year, end.year + 1))

    # Schulferien Bayern 2025/2026 (manuell, kein öffentliche API)
    school_holidays = [
        ("2025-04-14", "2025-04-25"),  # Osterferien
        ("2025-06-06", "2025-06-06"),  # Pfingstfreitag
        ("2025-07-30", "2025-09-10"),  # Sommerferien
        ("2025-11-03", "2025-11-07"),  # Herbstferien
        ("2025-12-22", "2026-01-05"),  # Weihnachtsferien
        ("2026-02-23", "2026-03-06"),  # Faschingsferien
        ("2026-04-06", "2026-04-18"),  # Osterferien
    ]

    school_ranges = []
    for s, e in school_holidays:
        school_ranges.append(pd.date_range(s, e, freq="D"))

    school_days = set()
    for r in school_ranges:
        school_days.update(r)

    rows = []
    for date in date_range:
        rows.append({
            "date_local":        date.date(),
            "is_public_holiday": date in by_holidays,
            "is_school_holiday": date in school_days,
            "holiday_name":      by_holidays.get(date, None),
        })

    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = fetch_all()
    from etl.loaders.postgres import load_holidays
    load_holidays(df)