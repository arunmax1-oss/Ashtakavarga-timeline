import pandas as pd
import plotly.express as px

# Base RGB color palette per Tier
TIER_BASE_RGB = {
    "1. Dasha / Pratyantar": (74, 144, 226),    # Blue
    "2. Jupiter Kakshya": (245, 166, 35),       # Gold
    "3. Mars Spark": (208, 2, 27),              # Red
    "4. Moon Trigger (6.75h)": (80, 227, 194)  # Cyan
}

def calculate_composite_score(sav, bav, lord_bindu, dasha_weight=1.0):
    """Calculates composite power score and checks critical thresholds."""
    if lord_bindu == 0:
        return 0, "Muted (No Kakshya Bindu)"
    
    score = sav * bav * dasha_weight
    if sav >= 28 and bav >= 4:
        return score, "High Precision Trigger"
    elif sav >= 28 or bav >= 4:
        return score, "Moderate Support"
    else:
        return score, "Low Support (<28 SAV)"

def build_precision_gantt_html(dasha_data, jup_data, mars_data, moon_data, output_file="index.html"):
    records = []

    # 1. Macro Tier
    score, status = calculate_composite_score(dasha_data['sav'], dasha_data['bav'], 1, 1.2)
    records.append({
        "Tier": "1. Dasha / Pratyantar",
        "Event": dasha_data["label"],
        "Start": dasha_data["start"],
        "End": dasha_data["end"],
        "Sign_Lord": dasha_data["lord"],
        "SAV": f"{dasha_data['sav']} bindus",
        "BAV": f"{dasha_data['bav']} / 8",
        "Bindu": "1 (Active Dasha)",
        "Composite_Score": round(score, 1),
        "Status": status,
        "Raw_SAV": dasha_data['sav']
    })

    # 2. Jupiter Kakshya Windows
    for jup in jup_data:
        score, status = calculate_composite_score(jup['sav'], jup['bav'], jup['lord_bindu'], 1.0)
        records.append({
            "Tier": "2. Jupiter Kakshya",
            "Event": f"Jupiter in {jup['sign']} ({jup['lord']} Kakshya)",
            "Start": jup["start"],
            "End": jup["end"],
            "Sign_Lord": f"{jup['sign']} / {jup['lord']}",
            "SAV": f"{jup['sav']} bindus",
            "BAV": f"{jup['bav']} / 8",
            "Bindu": "1 (Present)" if jup['lord_bindu'] == 1 else "0 (Absent)",
            "Composite_Score": round(score, 1),
            "Status": status,
            "Raw_SAV": jup['sav']
        })

    # 3. Mars Kinetic Sparks
    for mars in mars_data:
        score, status = calculate_composite_score(mars['sav'], mars['bav'], mars['lord_bindu'], 0.9)
        records.append({
            "Tier": "3. Mars Spark",
            "Event": f"Mars Spark ({mars['lord']} Kakshya)",
            "Start": mars["start"],
            "End": mars["end"],
            "Sign_Lord": f"{mars['sign']} / {mars['lord']}",
            "SAV": f"{mars['sav']} bindus",
            "BAV": f"{mars['bav']} / 8",
            "Bindu": "1 (Present)" if mars['lord_bindu'] == 1 else "0 (Absent)",
            "Composite_Score": round(score, 1),
            "Status": status,
            "Raw_SAV": mars['sav']
        })

    # 4. Moon Sub-Day Triggers
    for moon in moon_data:
        score, status = calculate_composite_score(moon['sav'], moon['bav'], moon['lord_bindu'], 0.8)
        records.append({
            "Tier": "4. Moon Trigger (6.75h)",
            "Event": f"Moon Trigger ({moon['lord']} Kakshya)",
            "Start": moon["start"],
            "End": moon["end"],
            "Sign_Lord": f"{moon['sign']} / {moon['lord']}",
            "SAV": f"{moon['sav']} bindus",
            "BAV": f"{moon['bav']} / 8",
            "Bindu": "1 (Present)" if moon['lord_bindu'] == 1 else "0 (Absent)",
            "Composite_Score": round(score, 1),
            "Status": status,
            "Raw_SAV": moon['sav']
        })

    df = pd.DataFrame(records)
    df["Span"] = (pd.to_datetime(df["Start"]).dt.strftime("%b %d, %H:%M") + " ➔ "
                  + pd.to_datetime(df["End"]).dt.strftime("%b %d, %H:%M"))

    # Dynamic Color & Opacity Assignment based on composite validity
    def assign_color(row):
        rgb = TIER_BASE_RGB.get(row["Tier"], (150, 150, 150))
        alpha = 1.0 if row["Raw_SAV"] >= 28 and "Muted" not in row["Status"] else 0.3
        cat = f"{row['Tier']} ({'Valid' if alpha == 1.0 else 'Muted'})"
        return pd.Series([cat, f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{alpha})"])

    df[["Category", "RGBA"]] = df.apply(assign_color, axis=1)
    color_map = dict(zip(df["Category"], df["RGBA"]))

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="End",
        y="Tier",
        color="Category",
        color_discrete_map=color_map,
        hover_name="Event",
        custom_data=["Sign_Lord", "SAV", "BAV", "Bindu", "Composite_Score", "Status", "Span"],
        title="<b>Ashtakavarga Precision Timing Engine</b>"
    )

    hovertemplate = (
        "<b>%{hovertext}</b><br>"
        "───────────────────────────────<br>"
        "⏱️ <b>Span:</b> %{customdata[6]}<br>"
        "🪐 <b>Sign / Kakshya Lord:</b> %{customdata[0]}<br>"
        "📊 <b>SAV Total:</b> %{customdata[1]} | <b>BAV:</b> %{customdata[2]}<br>"
        "✨ <b>Kakshya Lord Bindu:</b> <b>%{customdata[3]}</b><br>"
        "⚡ <b>Composite Power Score:</b> <b>%{customdata[4]}</b><br>"
        "🎯 <b>Evaluation:</b> <i>%{customdata[5]}</i>"
        "<extra></extra>"
    )

    fig.update_traces(hovertemplate=hovertemplate)
    fig.update_yaxes(autorange="reversed", title_text="")
    fig.update_xaxes(title_text="Timeline Window", rangeslider_visible=True, type="date")

    fig.update_layout(
        template="plotly_dark",
        height=520,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Export as standalone HTML
    fig.write_html(output_file, full_html=True, include_plotlyjs="cdn")
    print(f"Successfully generated static HTML web app: {output_file}")

# Sample Execution
if __name__ == "__main__":
    dasha = {"label": "Jupiter-Saturn-Mercury Dasha", "start": "2026-10-01 00:00", "end": "2026-12-31 23:59", "lord": "Jupiter / Merc", "sav": 32, "bav": 6}
    jup = [{"sign": "Cancer", "lord": "Mars", "start": "2026-10-10 00:00", "end": "2026-11-05 23:59", "sav": 32, "bav": 5, "lord_bindu": 1}]
    mars = [{"sign": "Scorpio", "lord": "Jupiter", "start": "2026-11-02 00:00", "end": "2026-11-07 23:59", "sav": 30, "bav": 4, "lord_bindu": 1}]
    moon = [
        {"sign": "Scorpio", "lord": "Moon", "start": "2026-11-03 08:00", "end": "2026-11-03 14:45", "sav": 30, "bav": 5, "lord_bindu": 1},
        {"sign": "Libra", "lord": "Sun", "start": "2026-11-18 02:00", "end": "2026-11-18 08:45", "sav": 21, "bav": 2, "lord_bindu": 0}
    ]

    build_precision_gantt_html(dasha, jup, mars, moon, "index.html")