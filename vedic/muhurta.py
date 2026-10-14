"""Muhurta (activity planner): find the best days for an activity over the coming weeks.

Each day starts from the personal day rating (vedic.weekly.day_forecast: Tara Bala, Chandra Bala, Moon
Ashtakavarga, tithi, weekday lord) and adds the classical activity rules: the nakshatra groups suited to
the activity, favourable weekdays, and tithis to avoid. Chandrashtama and the three hardest Taras
(Vipat, Pratyari, Naidhana) rule a day out. Rahu Kalam is shown so the slot can be avoided.
"""
import datetime as dt

from .weekly import day_forecast

# Classical nakshatra groups
FIXED = ["Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada"]           # Dhruva
MOVABLE = ["Punarvasu", "Swati", "Shravana", "Dhanishta", "Shatabhisha"]                  # Chara
SWIFT = ["Ashwini", "Pushya", "Hasta"]                                                     # Kshipra
SOFT = ["Mrigashira", "Chitra", "Anuradha", "Revati"]                                      # Mridu

ACTIVITIES = {
    "Start a new job or business": {
        "nakshatras": FIXED + SWIFT + ["Anuradha", "Revati", "Chitra"],
        "weekdays": ["Wednesday", "Thursday", "Friday", "Sunday"],
        "why": "Fixed and swift stars favour lasting, quick-moving enterprises.",
    },
    "Sign a contract or agreement": {
        "nakshatras": FIXED + SWIFT + SOFT,
        "weekdays": ["Wednesday", "Thursday", "Friday"],
        "why": "Mercury (contracts), Jupiter (good faith) and Venus (agreement) days with stable stars.",
    },
    "Travel or relocation": {
        "nakshatras": MOVABLE + SWIFT + ["Mrigashira", "Anuradha", "Revati"],
        "weekdays": ["Monday", "Wednesday", "Thursday", "Friday"],
        "why": "Movable and swift stars suit journeys; Revati protects travellers.",
    },
    "Buy property or a vehicle": {
        "nakshatras": FIXED + SOFT + ["Pushya", "Punarvasu"],
        "weekdays": ["Monday", "Thursday", "Friday"],
        "why": "Fixed stars for permanence, soft stars for comfort; Venus and Jupiter days.",
    },
    "Financial investment": {
        "nakshatras": FIXED + SWIFT + ["Punarvasu", "Shravana", "Dhanishta", "Revati"],
        "weekdays": ["Wednesday", "Thursday", "Friday"],
        "why": "Steady and swift stars on Mercury, Jupiter and Venus days.",
    },
    "Start studies or a course": {
        "nakshatras": SWIFT + ["Punarvasu", "Chitra", "Swati", "Shravana", "Revati", "Mrigashira"],
        "weekdays": ["Wednesday", "Thursday", "Sunday"],
        "why": "Mercury and Jupiter days with the classical learning stars.",
    },
    "Medical procedure or treatment": {
        "nakshatras": SWIFT + SOFT + FIXED,
        "weekdays": ["Monday", "Wednesday", "Thursday", "Friday"],
        "why": "Swift stars (Ashwini is the healers' star) and gentle soft stars.",
    },
    "Engagement or important relationship step": {
        "nakshatras": FIXED + SOFT + ["Magha", "Hasta", "Swati", "Moola"],
        "weekdays": ["Monday", "Wednesday", "Thursday", "Friday"],
        "why": "The classical marriage stars on benefic weekdays.",
    },
    "Housewarming (griha pravesh)": {
        "nakshatras": FIXED + SOFT + ["Pushya", "Dhanishta", "Shatabhisha"],
        "weekdays": ["Monday", "Wednesday", "Thursday", "Friday"],
        "why": "Fixed stars give stability to a home; avoid Tuesdays and Saturdays.",
    },
}
HARD_TARAS = ["Vipat", "Pratyari", "Naidhana"]


def score_day(day, activity):
    rules = ACTIVITIES[activity]
    reasons, score = [], day["score"]
    if day["chandrashtama"]:
        return None, ["Chandrashtama (Moon 8th from your natal Moon)"]
    if day["tara"]["name"] in HARD_TARAS:
        return None, [f"{day['tara']['name']} tara"]
    if day["tithi"]["group"] in ("Rikta", "Amavasya"):
        return None, [f"{day['tithi']['name']} (a {day['tithi']['group']} tithi)"]
    if day["nakshatra"] in rules["nakshatras"]:
        score += 3
        reasons.append(f"{day['nakshatra']} suits this activity")
    if day["weekday"] in rules["weekdays"]:
        score += 1
        reasons.append(f"{day['weekday']} is a favourable weekday")
    if day["tithi"]["group"] in ("Purna", "Jaya", "Bhadra"):
        score += 1
        reasons.append(f"{day['tithi']['group']} tithi ({day['tithi']['group_use']})")
    return score, reasons


def find_days(chart, av, schedule, activity, start, days, tz_name, place=None, top=8):
    """Best days for `activity` in `days` days from `start`. Returns (best, ruled_out_count)."""
    candidates, ruled_out = [], 0
    for i in range(days):
        d = day_forecast(chart, av, schedule, start + dt.timedelta(days=i), tz_name, place)
        score, reasons = score_day(d, activity)
        if score is None:
            ruled_out += 1
            continue
        candidates.append({**d, "muhurta_score": score, "muhurta_reasons": reasons})
    best = sorted(candidates, key=lambda d: (-d["muhurta_score"], d["date"]))[:top]
    return sorted(best, key=lambda d: d["date"]), ruled_out
