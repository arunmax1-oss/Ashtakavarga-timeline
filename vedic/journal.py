"""Prediction journal: record what actually happened and compare it with the app's day ratings.

The same file also holds the remedy log (rows with kind "remedy"): which planet's remedy was practised, how
(mantra, charity, fast...) and how many repetitions. Journal files saved before the log existed still load.
"""
import datetime as dt
import io

import pandas as pd

COLUMNS = ["date", "area", "event", "felt", "kind", "planet", "practice", "count"]
REQUIRED = ["date", "area", "event", "felt"]
PRACTICES = ["Mantra (japa)", "Charity", "Fasting", "Hymn (stotra)", "Practical step", "Temple visit or puja",
             "Wearing gemstone"]
# Journal areas -> the life-area pages they belong to
AREA_TO_LIFE = {"Career": ["Job"], "Money": ["Wealth"], "Relationships": ["Relationships"],
                "Family": ["Home & Family", "Children"], "Health": ["Health"], "Studies": ["Education"],
                "Travel": ["Travel & Foreign"], "Spiritual": ["Spirituality"]}
AREAS = ["Career", "Money", "Relationships", "Family", "Health", "Studies", "Travel", "Spiritual", "Other"]
FELT = {2: "Very good", 1: "Good", 0: "Neutral", -1: "Difficult", -2: "Very difficult"}


def empty():
    return pd.DataFrame(columns=COLUMNS)


def from_csv(file):
    df = pd.read_csv(file)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"The file is missing columns: {', '.join(missing)}")
    for col, default in (("kind", "event"), ("planet", ""), ("practice", ""), ("count", 0)):
        if col not in df.columns:
            df[col] = default
    df = df[COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["felt"] = df["felt"].fillna(0).astype(int).clip(-2, 2)
    df["count"] = df["count"].fillna(0).astype(int)
    for col in ("event", "planet", "practice"):
        df[col] = df[col].astype(object).where(df[col].notna(), "").astype(str)
    df["kind"] = df["kind"].astype(object).where(df["kind"].notna(), "event").astype(str).replace("", "event")
    return df


def to_csv(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def _append(df, row):
    full = {"kind": "event", "planet": "", "practice": "", "count": 0, **row}
    return pd.concat([df, pd.DataFrame([full])], ignore_index=True).sort_values("date", kind="stable") \
        .reset_index(drop=True)


def add(df, date, area, event, felt):
    return _append(df, {"date": date, "area": area, "event": event, "felt": int(felt)})


def add_remedy(df, date, planet, practice, count=0, note=""):
    return _append(df, {"date": date, "area": "Remedy", "event": note, "felt": 0, "kind": "remedy",
                        "planet": planet, "practice": practice, "count": int(count)})


def events(df):
    return df[df["kind"] != "remedy"].reset_index(drop=True) if "kind" in df else df


def remedy_log(df):
    return df[df["kind"] == "remedy"].reset_index(drop=True) if "kind" in df else df.iloc[0:0]


def remedy_progress(df, planet, japa_target, weekday):
    """Practice summary for one planet: sessions, days, japa total vs the traditional course, current daily
    streak, sessions on the planet's own weekday (Monday = 0) and the first and last dates."""
    log = remedy_log(df)
    log = log[log["planet"] == planet]
    if log.empty:
        return None
    days = sorted(set(log["date"]))
    streak, d = 0, days[-1]
    while d in set(days):
        streak, d = streak + 1, d - dt.timedelta(days=1)
    japa = int(log.loc[log["practice"] == "Mantra (japa)", "count"].sum())
    return {"sessions": len(log), "days": len(days), "first": days[0], "last": days[-1],
            "japa": japa, "japa_target": japa_target, "japa_pct": min(1.0, japa / japa_target) if japa_target else 0,
            "streak": streak, "on_weekday": sum(1 for x in log["date"] if x.weekday() == weekday),
            "by_practice": log.groupby("practice").size().to_dict()}


def remedy_effect(df, planet, life_areas, min_entries=2):
    """How journal events in the planet's life areas felt before vs since its remedy began.
    None until there are at least `min_entries` on each side."""
    log = remedy_log(df)
    log = log[log["planet"] == planet]
    if log.empty:
        return None
    start = min(log["date"])
    areas = [a for a, lives in AREA_TO_LIFE.items() if set(lives) & set(life_areas)]
    ev = events(df)
    ev = ev[ev["area"].isin(areas)]
    before, after = ev[ev["date"] < start]["felt"], ev[ev["date"] >= start]["felt"]
    out = {"start": start, "areas": areas, "n_before": len(before), "n_after": len(after),
           "before": before.mean() if len(before) else None, "after": after.mean() if len(after) else None}
    out["ready"] = len(before) >= min_entries and len(after) >= min_entries
    return out


def evaluate(df, rate_day):
    """rate_day(date) -> day forecast dict. Adds the app's rating to each entry and summarises agreement."""
    df = events(df)
    rows = []
    for _, e in df.iterrows():
        d = e["date"] if isinstance(e["date"], dt.date) else pd.to_datetime(e["date"]).date()
        f = rate_day(d)
        agree = (e["felt"] > 0 and f["score"] > 0) or (e["felt"] < 0 and f["score"] < 0) or \
                (e["felt"] == 0 and -1 <= f["score"] <= 1)
        rows.append({"Date": d, "Area": e["area"], "What happened": e["event"], "How it felt": FELT[int(e["felt"])],
                     "App rating": f["rating"], "App score": f["score"], "Tara": f["tara"]["name"],
                     "Moon from natal Moon": f["from_moon"], "Agree": "✓" if agree else "✗"})
    out = pd.DataFrame(rows)
    if out.empty:
        return out, None
    good = out[df["felt"].values > 0]["App score"]
    bad = out[df["felt"].values < 0]["App score"]
    summary = {
        "entries": len(out), "agreement": (out["Agree"] == "✓").mean(),
        "avg_score_good": good.mean() if len(good) else None, "avg_score_bad": bad.mean() if len(bad) else None,
    }
    return out, summary
