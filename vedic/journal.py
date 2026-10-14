"""Prediction journal: record what actually happened and compare it with the app's day ratings."""
import datetime as dt
import io

import pandas as pd

COLUMNS = ["date", "area", "event", "felt"]
AREAS = ["Career", "Money", "Relationships", "Family", "Health", "Studies", "Travel", "Spiritual", "Other"]
FELT = {2: "Very good", 1: "Good", 0: "Neutral", -1: "Difficult", -2: "Very difficult"}


def empty():
    return pd.DataFrame(columns=COLUMNS)


def from_csv(file):
    df = pd.read_csv(file)
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"The file is missing columns: {', '.join(missing)}")
    df = df[COLUMNS].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["felt"] = df["felt"].astype(int).clip(-2, 2)
    df["event"] = df["event"].fillna("").astype(str)
    return df


def to_csv(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def add(df, date, area, event, felt):
    row = pd.DataFrame([{"date": date, "area": area, "event": event, "felt": int(felt)}])
    return pd.concat([df, row], ignore_index=True).sort_values("date").reset_index(drop=True)


def evaluate(df, rate_day):
    """rate_day(date) -> day forecast dict. Adds the app's rating to each entry and summarises agreement."""
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
