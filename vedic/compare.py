"""Compare this app's positions with positions pasted from other software (Jagannatha Hora, etc.)."""
import re

from .constants import SIGNS

ALIASES = {
    "Ascendant": ["ascendant", "asc", "lagna", "la", "lg"], "Sun": ["sun", "su", "surya"],
    "Moon": ["moon", "mo", "chandra"], "Mars": ["mars", "ma", "kuja", "mangal"],
    "Mercury": ["mercury", "me", "budha", "merc"], "Jupiter": ["jupiter", "ju", "guru", "jup"],
    "Venus": ["venus", "ve", "shukra", "ven"], "Saturn": ["saturn", "sa", "shani", "sat"],
    "Rahu": ["rahu", "ra"], "Ketu": ["ketu", "ke"],
}
_SIGN_KEYS = ({s.lower(): i for i, s in enumerate(SIGNS)} | {s[:3].lower(): i for i, s in enumerate(SIGNS)}
              | {c: i for i, c in enumerate(["ar", "ta", "ge", "cn", "le", "vi", "li", "sc", "sg", "cp", "aq", "pi"])})


def parse_positions(text):
    """Parse lines like 'Sun 0°33' Gemini', 'Moon Ari 25:29:24', 'Mars 70.30' (absolute longitude).

    Returns ({body: longitude}, [lines that could not be read])."""
    found, bad = {}, []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        words = re.findall(r"[A-Za-z]+", line)
        body = next((b for w in words for b, al in ALIASES.items() if w.lower() in al), None)
        sign = next((_SIGN_KEYS[w.lower()] for w in words if w.lower() in _SIGN_KEYS), None)
        nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", line)]
        if body is None or not nums:
            bad.append(raw)
            continue
        d, m, s = (nums + [0, 0])[:3]
        value = d + m / 60 + s / 3600
        if sign is not None:
            found[body] = (sign * 30 + value) % 360
        elif value < 360:
            found[body] = value
        else:
            bad.append(raw)
    return found, bad


def compare(chart, theirs):
    rows = []
    for body, lon in theirs.items():
        ours = chart["planets"][body]["lon"]
        diff = ((ours - lon + 180) % 360) - 180
        rows.append({"Body": body, "This app": f"{SIGNS[int(ours // 30)]} {ours % 30:.2f}°",
                     "Other software": f"{SIGNS[int(lon // 30)]} {lon % 30:.2f}°",
                     "Difference (arc-min)": round(diff * 60, 1),
                     "Same sign": "✓" if int(ours // 30) == int(lon // 30) else "✗",
                     "Verdict": "match" if abs(diff) * 60 <= 2 else "small" if abs(diff) * 60 <= 15 else "check"})
    return rows


def diagnose(rows):
    """Explain the usual causes of a systematic difference."""
    if not rows:
        return ""
    diffs = [r["Difference (arc-min)"] for r in rows if r["Body"] != "Ascendant"]
    if len(diffs) >= 2 and max(diffs) - min(diffs) < 3 and abs(sum(diffs) / len(diffs)) > 2:
        return (f"All planets differ by about {sum(diffs) / len(diffs):+.1f}′ together: that is an **ayanamsha** "
                "difference. Match the ayanamsha setting (Lahiri, Raman or KP) to the other software.")
    nodes = [r for r in rows if r["Body"] in ("Rahu", "Ketu") and abs(r["Difference (arc-min)"]) > 15]
    asc = [r for r in rows if r["Body"] == "Ascendant" and abs(r["Difference (arc-min)"]) > 15]
    notes = []
    if nodes:
        notes.append("Rahu/Ketu differ: the other software probably uses the **true node**; switch the Rahu/Ketu "
                     "setting.")
    if asc:
        notes.append("The Ascendant differs but planets match: check the **birth time, time zone or coordinates**.")
    return " ".join(notes) or "Positions agree within normal rounding."
