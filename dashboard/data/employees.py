# dashboard/data/employees.py
#
# Mitarbeiterliste mit wöchentlichem Schichtplan.
# Einfach hier anpassen wenn sich was ändert.
#
# Schichtzeiten als ("HH:MM", "HH:MM") oder None wenn kein Dienst.

EMPLOYEES = [
    {
        "id":   "AK",
        "name": "Anna K.",
        "role": "Kassierer",
        "shifts": {
            "Mon": ("08:00", "14:00"),
            "Tue": ("08:00", "14:00"),
            "Wed": ("12:00", "20:00"),
            "Thu": None,
            "Fri": ("08:00", "14:00"),
            "Sat": ("10:00", "16:00"),
            "Sun": None,
        },
    },
    {
        "id":   "TM",
        "name": "Thomas M.",
        "role": "Abteilungsleiter",
        "shifts": {
            "Mon": ("08:00", "16:00"),
            "Tue": ("08:00", "16:00"),
            "Wed": ("08:00", "16:00"),
            "Thu": ("08:00", "16:00"),
            "Fri": ("08:00", "16:00"),
            "Sat": None,
            "Sun": None,
        },
    },
    {
        "id":   "SB",
        "name": "Sara B.",
        "role": "Kassierer",
        "shifts": {
            "Mon": ("10:00", "18:00"),
            "Tue": None,
            "Wed": ("10:00", "18:00"),
            "Thu": ("10:00", "18:00"),
            "Fri": ("10:00", "18:00"),
            "Sat": ("08:00", "14:00"),
            "Sun": None,
        },
    },
    {
        "id":   "MR",
        "name": "Max R.",
        "role": "Lagerist",
        "shifts": {
            "Mon": ("06:00", "14:00"),
            "Tue": ("06:00", "14:00"),
            "Wed": None,
            "Thu": ("06:00", "14:00"),
            "Fri": ("06:00", "14:00"),
            "Sat": ("06:00", "12:00"),
            "Sun": None,
        },
    },
    {
        "id":   "LW",
        "name": "Lisa W.",
        "role": "Kassierer",
        "shifts": {
            "Mon": None,
            "Tue": ("14:00", "20:00"),
            "Wed": ("14:00", "20:00"),
            "Thu": ("14:00", "20:00"),
            "Fri": ("14:00", "20:00"),
            "Sat": ("12:00", "20:00"),
            "Sun": None,
        },
    },
    {
        "id":   "KS",
        "name": "Klaus S.",
        "role": "Abteilungsleiter",
        "shifts": {
            "Mon": None,
            "Tue": None,
            "Wed": ("12:00", "20:00"),
            "Thu": ("12:00", "20:00"),
            "Fri": ("12:00", "20:00"),
            "Sat": ("10:00", "18:00"),
            "Sun": None,
        },
    },
]