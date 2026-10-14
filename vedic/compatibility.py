"""Ashtakoota (guna milan) compatibility out of 36 points, plus a Manglik (Kuja dosha) check.

Inputs are two charts; the matching uses each person's Moon sign and nakshatra. Classical matching is
read from the groom's side for Varna, Vashya, Gana and the Tara direction, so the person roles matter.
Several koota tables (especially Vashya and Gana) vary slightly between traditions; the common North
Indian values are used and stated here.
"""
from .aspects import aspects_on
from .constants import NAKSHATRA_SPAN, NAKSHATRAS, SIGNS, SIGN_LORDS
from .shadbala import NATURAL_FRIENDS

VARNA = {3: 3, 7: 3, 11: 3, 0: 2, 4: 2, 8: 2, 1: 1, 5: 1, 9: 1, 2: 0, 6: 0, 10: 0}  # 3 = Brahmin ... 0 = Shudra
VARNA_NAMES = ["Shudra", "Vaishya", "Kshatriya", "Brahmin"]

YONI_OF = ["Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat", "Rat", "Rat", "Cow",
           "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer", "Dog", "Monkey", "Mongoose", "Monkey", "Lion",
           "Horse", "Lion", "Cow", "Elephant"]
YONI_ORDER = ["Horse", "Elephant", "Sheep", "Serpent", "Dog", "Cat", "Rat", "Cow", "Buffalo", "Tiger", "Deer",
              "Monkey", "Mongoose", "Lion"]
YONI_TABLE = [
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1],
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
    [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],
    [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],
    [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1],
    [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],
    [3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],
    [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],
    [1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4],
]

GANA_OF = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa", "Rakshasa",
           "Manushya", "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya",
           "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"]
GANA_POINTS = {("Deva", "Deva"): 6, ("Deva", "Manushya"): 6, ("Deva", "Rakshasa"): 1,
               ("Manushya", "Deva"): 5, ("Manushya", "Manushya"): 6, ("Manushya", "Rakshasa"): 0,
               ("Rakshasa", "Deva"): 1, ("Rakshasa", "Manushya"): 0, ("Rakshasa", "Rakshasa"): 6}

VASHYA_GROUPS = ["Chatushpada (quadruped)", "Manava (human)", "Jalachara (water)", "Vanachara (wild)",
                 "Keeta (insect)"]
VASHYA_POINTS = [  # groom group (row) vs bride group (column)
    [2, 1, 1, 0.5, 1],
    [1, 2, 0.5, 0, 1],
    [1, 0.5, 2, 1, 1],
    [0, 0, 0, 2, 0],
    [1, 1, 1, 0, 2],
]
NADI_NAMES = ["Adi (Vata)", "Madhya (Pitta)", "Antya (Kapha)"]
TARA_NAMES = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyari", "Sadhana", "Naidhana", "Mitra", "Parama Mitra"]


def _moon(chart):
    lon = chart["planets"]["Moon"]["lon"]
    return {"sign": int(lon // 30), "nak": int(lon // NAKSHATRA_SPAN), "degree": lon % 30}


def vashya_group(sign, degree):
    if sign in (0, 1):
        return 0
    if sign == 8:
        return 1 if degree < 15 else 0
    if sign == 9:
        return 0 if degree < 15 else 2
    if sign in (2, 5, 6, 10):
        return 1
    if sign in (3, 11):
        return 2
    return 3 if sign == 4 else 4  # Leo wild, Scorpio insect


def nadi(nak):
    pos = nak % 6
    return 0 if pos in (0, 5) else 1 if pos in (1, 4) else 2


def _relation(a, b):
    friends, neutrals, _ = NATURAL_FRIENDS[a]
    return "friend" if b in friends else "neutral" if b in neutrals else "enemy"


def ashtakoota(groom, bride):
    g, b = _moon(groom), _moon(bride)
    rows = []

    gv, bv = VARNA[g["sign"]], VARNA[b["sign"]]
    rows.append(("Varna", 1, 1 if gv >= bv else 0, f"{VARNA_NAMES[gv]} / {VARNA_NAMES[bv]}",
                 "Spiritual and ego compatibility"))

    gw, bw = vashya_group(g["sign"], g["degree"]), vashya_group(b["sign"], b["degree"])
    rows.append(("Vashya", 2, VASHYA_POINTS[gw][bw], f"{VASHYA_GROUPS[gw]} / {VASHYA_GROUPS[bw]}",
                 "Mutual attraction and influence"))

    t1 = ((b["nak"] - g["nak"]) % 27) % 9  # bride's star counted from the groom's
    t2 = ((g["nak"] - b["nak"]) % 27) % 9  # groom's star counted from the bride's
    good = [t not in (2, 4, 6) for t in (t1, t2)]
    rows.append(("Tara", 3, 3 if all(good) else 1.5 if any(good) else 0,
                 f"{TARA_NAMES[t2]} / {TARA_NAMES[t1]}", "Health and well-being of the couple"))

    gy, by = YONI_OF[g["nak"]], YONI_OF[b["nak"]]
    rows.append(("Yoni", 4, YONI_TABLE[YONI_ORDER.index(gy)][YONI_ORDER.index(by)], f"{gy} / {by}",
                 "Physical and intimate compatibility"))

    gl, bl = SIGN_LORDS[SIGNS[g["sign"]]], SIGN_LORDS[SIGNS[b["sign"]]]
    if gl == bl:
        maitri = 5
    else:
        pair = sorted([_relation(gl, bl), _relation(bl, gl)])
        maitri = {("friend", "friend"): 5, ("friend", "neutral"): 4, ("neutral", "neutral"): 3,
                  ("enemy", "friend"): 1, ("enemy", "neutral"): 0.5, ("enemy", "enemy"): 0}[tuple(pair)]
    rows.append(("Graha Maitri", 5, maitri, f"{gl} / {bl}", "Mental wavelength and friendship"))

    gg, bg = GANA_OF[g["nak"]], GANA_OF[b["nak"]]
    rows.append(("Gana", 6, GANA_POINTS[(gg, bg)], f"{gg} / {bg}", "Temperament"))

    dist = (b["sign"] - g["sign"]) % 12 + 1
    bad = dist in (2, 12, 5, 9, 6, 8)
    rows.append(("Bhakoot", 7, 0 if bad else 7, f"{SIGNS[g['sign']]} / {SIGNS[b['sign']]} ({dist}/{(14 - dist) % 12 or 12})",
                 "Family welfare, finances and growth together"))

    gn, bn = nadi(g["nak"]), nadi(b["nak"])
    rows.append(("Nadi", 8, 0 if gn == bn else 8, f"{NADI_NAMES[gn]} / {NADI_NAMES[bn]}",
                 "Health and progeny (the most heavily weighted koota)"))

    total = sum(r[2] for r in rows)
    verdict = ("Excellent match" if total >= 28 else "Very good match" if total >= 24 else
               "Good match" if total >= 18 else "Below the traditional minimum of 18")
    notes = []
    if gn == bn:
        notes.append("Nadi dosha (same Nadi): traditionally the most serious mismatch. It is considered cancelled "
                     "when both share the same Moon sign but different nakshatras, or the same nakshatra in "
                     "different signs." + (" **That exception applies here.**" if (g["sign"] == b["sign"]) != (g["nak"] == b["nak"]) else ""))
    if bad:
        notes.append("Bhakoot dosha: considered cancelled if the two Moon-sign lords are the same or friends."
                     + (" **That exception applies here.**" if gl == bl or maitri >= 4 else ""))
    return {"rows": [{"Koota": r[0], "Max": r[1], "Points": r[2], "Groom / Bride": r[3], "Governs": r[4]} for r in rows],
            "total": total, "verdict": verdict, "notes": notes,
            "groom_star": NAKSHATRAS[g["nak"]], "bride_star": NAKSHATRAS[b["nak"]]}


def manglik(chart):
    """Mars in the 1st, 2nd, 4th, 7th, 8th or 12th from Lagna or Moon (Kuja dosha), with common cancellations."""
    p = chart["planets"]
    mars = p["Mars"]
    from_lagna = mars["house"]
    from_moon = (mars["sign_idx"] - p["Moon"]["sign_idx"]) % 12 + 1
    houses = (1, 2, 4, 7, 8, 12)
    by = [label for label, h in (("Lagna", from_lagna), ("Moon", from_moon)) if h in houses]
    cancel = []
    if mars["sign"] in ("Aries", "Scorpio", "Capricorn"):
        cancel.append(f"Mars is in {mars['sign']} (own or exaltation sign)")
    if any(n == "Jupiter" for n, _ in aspects_on(chart, "Mars")) or p["Jupiter"]["sign_idx"] == mars["sign_idx"]:
        cancel.append("Jupiter aspects or joins Mars")
    return {"manglik": bool(by), "from": by, "house_lagna": from_lagna, "house_moon": from_moon, "cancellations": cancel}
