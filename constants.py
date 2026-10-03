"""Static astrological reference data. No calculations live here."""

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

# The seven classical planets (used for Ashtakavarga and Chara Karakas).
CLASSICAL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
ALL_PLANETS = CLASSICAL_PLANETS + ["Rahu", "Ketu"]

EXALTATION_SIGNS = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn", "Mercury": "Virgo",
    "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra", "Rahu": "Taurus", "Ketu": "Scorpio",
}

DEBILITATION_SIGNS = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries", "Rahu": "Scorpio", "Ketu": "Taurus",
}

OWN_SIGNS = {
    "Sun": ["Leo"], "Moon": ["Cancer"], "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"], "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"], "Saturn": ["Capricorn", "Aquarius"],
    "Rahu": ["Aquarius"], "Ketu": ["Scorpio"],
}

# Directional strength (Dig Bala): house where each planet is strongest.
DIG_BALA_HOUSE = {"Jupiter": 1, "Mercury": 1, "Moon": 4, "Venus": 4, "Saturn": 7, "Sun": 10, "Mars": 10}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_SPAN = 360.0 / 27.0

# Vimshottari order starting from Ashwini; repeats every 9 nakshatras.
DASHA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
DASHA_TOTAL_YEARS = 120
DAYS_PER_YEAR = 365.25

HOUSE_INFO = {
    1: ("1st (Lagna)", "Self, Physical Health, Vitality & Identity"),
    2: ("2nd (Dhana)", "Accumulated Wealth, Speech & Family Assets"),
    3: ("3rd (Vikrama)", "Courage, Initiatives, Siblings & Short Journeys"),
    4: ("4th (Matri)", "Home, Peace of Mind, Property & Mother"),
    5: ("5th (Putra)", "Intelligence, Creativity, Children & Speculation"),
    6: ("6th (Ari)", "Debts, Disease, Obstacles & Daily Work Friction"),
    7: ("7th (Yuvati)", "Partnerships, Marriage & Foreign Commerce"),
    8: ("8th (Randhra)", "Longevity, Transformation, Sudden Events & Research"),
    9: ("9th (Dharma)", "Higher Knowledge, Fortune, Father & Mentorship"),
    10: ("10th (Karma)", "Career Status, Public Standing & Authority"),
    11: ("11th (Labha)", "Gains, Income, Professional Network & Wish Fulfillment"),
    12: ("12th (Vyaya)", "Expenses, Losses, Foreign Lands & Spiritual Solitude"),
}

AYANAMSHAS = ["Lahiri (Chitrapaksha)", "Raman", "Krishnamurti (KP)"]

PLANET_COLORS = {
    "Sun": "#E8A33D", "Moon": "#50E3C2", "Mars": "#D0453B", "Mercury": "#3FB37F",
    "Jupiter": "#F5C242", "Venus": "#C77DDB", "Saturn": "#5B7DB1",
    "Rahu": "#8C8C8C", "Ketu": "#A0785A", "Dasha": "#4A90E2",
}


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
