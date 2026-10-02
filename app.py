"""
Astrology Analysis Engine & Dashboard
Filename: app.py
Run command: python app.py
Dependencies: pip install flask
"""

from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# =====================================================================
# 1. ASTROLOGICAL ENGINE & DATA DICTIONARIES
# =====================================================================

DASHA_DESCRIPTIONS = {
    "Sun": "Focuses on ego integration, core identity, leadership, professional status, and authority dynamics.",
    "Moon": "Highlights emotional stability, public interactions, mind clarity, maternal ties, and shifting perceptions.",
    "Mars": "Drives ambition, physical execution, real estate, courage, and technical problem-solving.",
    "Rahu": "Triggers rapid worldly expansion, unconventional growth, digital/foreign horizons, and intense focus.",
    "Jupiter": "Expands wisdom, academic/philosophical depth, financial growth, mentorship, and legal alignment.",
    "Saturn": "Demands discipline, structure, accountability, long-term endurance, and systemic groundwork.",
    "Mercury": "Sharpens intellect, commercial transactions, strategic communication, analytics, and business ties.",
    "Ketu": "Induces internal reflection, detachment from outcomes, spiritual research, and pruning redundant paths.",
    "Venus": "Enhances artistic creation, luxury, wealth accumulation, partnership dynamics, and social refinement."
}

RELATIONSHIP_DESCRIPTIONS = {
    "1_7": "1/7 Axis (Direct Mutual Aspect): Creates dynamic interpersonal focus and active negotiation between personal goals and external partnerships.",
    "3_11": "3/11 Axis (Growth Alignment): Excellent flow for financial gains, skill acquisition, networking, and executing strategic initiatives with low friction.",
    "4_10": "4/10 Axis (Kendra Action): Focuses heavily on balancing internal security (home/foundations) with external output (career/reputation).",
    "5_9": "5/9 Axis (Trikona Prosperity): Highly auspicious period bringing creative flow, fortunate breakthroughs, intellectual clarity, and alignment.",
    "2_12": "2/12 Axis (Dwirdwadasa): Indicates higher financial churn, unexpected expenses, personal detachment, or long-distance shifts.",
    "6_8": "6/8 Axis (Shashtashtaka): Transformational period requiring conflict management, health vigilance, and structural adjustments."
}

class AstrologyEngine:
    @staticmethod
    def evaluate_dasha(mahadasha: str, antardasha: str, relationship: str) -> dict:
        maha_desc = DASHA_DESCRIPTIONS.get(mahadasha, "Standard lifecycle influence.")
        antar_desc = DASHA_DESCRIPTIONS.get(antardasha, "Standard sub-period manifestation.")
        rel_desc = RELATIONSHIP_DESCRIPTIONS.get(relationship, "Standard mutual placement interplay.")

        # Determine overall energy state
        if relationship in ["5_9", "3_11"]:
            dynamic = {"label": "Harmonious Period", "status": "success"}
        elif relationship in ["6_8", "2_12"]:
            dynamic = {"label": "Transformational / High Friction", "status": "warning"}
        else:
            dynamic = {"label": "Action Oriented", "status": "info"}

        summary = (
            f"Operating under {mahadasha} as overarching governor and {antardasha} as active operator. "
            f"Current period focuses daily energy on executing {antardasha}'s portfolio within {mahadasha}'s lifecycle bounds."
        )

        return {
            "summary": summary,
            "dynamic": dynamic,
            "mahadasha_narrative": f"Overarching Theme ({mahadasha}): {maha_desc}",
            "antardasha_narrative": f"Current Activation ({antardasha}): {antar_desc}",
            "relationship_narrative": f"Structural Interplay: {rel_desc}"
        }

    @staticmethod
    def evaluate_career_ashtakavarga(sav_10: int, sav_11: int, sav_12: int, bav_saturn: int, bav_sun: int) -> dict:
        # Benchmarks & Statuses
        status_10 = "Strong" if sav_10 >= 28 else "Challenging"
        status_11 = "Optimal Gains" if sav_11 >= sav_10 else "Leaking Value"
        status_12 = "Controlled Spend" if sav_12 < sav_11 else "Excess Expense"
        status_saturn = "High Perseverance" if bav_saturn >= 4 else "Low Endurance"
        status_sun = "Good Recognition" if bav_sun >= 4 else "Visibility Struggle"

        # Narrative Generation
        narrative = f"The 10th house holds {sav_10} SAV points. "
        if sav_10 >= 30:
            narrative += "This high score indicates strong natural momentum in professional endeavours, institutional backing, and resilience. "
        elif sav_10 >= 28:
            narrative += "This average score guarantees steady growth provided consistent effort is applied. "
        else:
            narrative += "This score suggests professional stability requires deliberate strategy, skill acquisition, and careful handling of authority. "

        if sav_11 > sav_10 and sav_11 > sav_12:
            narrative += f"The ideal prosperity hierarchy (11th house [{sav_11}] > 10th house [{sav_10}] > 12th house [{sav_12}]) is met, ensuring financial rewards exceed personal labor and overhead stays contained."
        else:
            narrative += f"Financial leakage is indicated as gains (11th house: {sav_11} pts) do not comfortably exceed expenses (12th house: {sav_12} pts)."

        return {
            "statuses": {
                "sav_10": status_10,
                "sav_11": status_11,
                "sav_12": status_12,
                "bav_saturn": status_saturn,
                "bav_sun": status_sun
            },
            "narrative": narrative
        }

    @staticmethod
    def evaluate_health_ashtakavarga(sav_1: int, sav_6: int, sav_8: int, bav_mars: int) -> dict:
        status_1 = "Robust" if sav_1 >= 28 else "Fragile"
        status_6 = "Low Risk" if sav_6 < sav_1 else "Elevated Vulnerability"
        status_8 = "Low Vulnerability" if sav_8 < 28 else "Transformation Focus"
        status_mars = "Optimal Stamina" if bav_mars >= 4 else "Needs Physical Discipline"

        narrative = f"The 1st House (Lagna) possesses {sav_1} SAV points against {sav_6} points in the 6th House. "
        if sav_1 >= sav_6:
            narrative += "Because vitality (1st house) exceeds disease indicators (6th house), the body possesses strong inherent immunity and recovers well. "
        else:
            narrative += "Because 6th house points surpass the 1st house, acute stress, inflammation, or lifestyle fatigue can compromise vitality. "

        if sav_8 > 30:
            narrative += f"The 8th house score is elevated ({sav_8} pts), indicating a need to monitor hormonal balance or chronic factors during major transits."
        else:
            narrative += f"The 8th house score ({sav_8} pts) remains controlled, indicating protection against sudden health crises."

        return {
            "statuses": {
                "sav_1": status_1,
                "sav_6": status_6,
                "sav_8": status_8,
                "bav_mars": status_mars
            },
            "narrative": narrative
        }


# =====================================================================
# 2. REST API ENDPOINTS
# =====================================================================

@app.route('/api/v1/dasha-narrative', methods=['POST'])
def api_dasha_narrative():
    data = request.get_json() or {}
    maha = data.get('mahadasha', 'Rahu')
    antar = data.get('antardasha', 'Jupiter')
    rel = data.get('relationship', '3_11')
    result = AstrologyEngine.evaluate_dasha(maha, antar, rel)
    return jsonify(result)

@app.route('/api/v1/ashtakavarga-eval', methods=['POST'])
def api_ashtakavarga_eval():
    data = request.get_json() or {}
    career_res = AstrologyEngine.evaluate_career_ashtakavarga(
        int(data.get('sav_10', 32)),
        int(data.get('sav_11', 34)),
        int(data.get('sav_12', 22)),
        int(data.get('bav_saturn', 5)),
        int(data.get('bav_sun', 4))
    )
    health_res = AstrologyEngine.evaluate_health_ashtakavarga(
        int(data.get('sav_1', 30)),
        int(data.get('sav_6', 24)),
        int(data.get('sav_8', 21)),
        int(data.get('bav_mars', 3))
    )
    return jsonify({
        "career": career_res,
        "health": health_res
    })


# =====================================================================
# 3. INTERACTIVE DASHBOARD HTML ROUTE
# =====================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Astrology Narrative Engine</title>
  <style>
    body { font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; }
    .container { max-width: 1000px; margin: auto; }
    .nav { display: flex; gap: 12px; margin-bottom: 20px; border-bottom: 2px solid #334155; }
    .nav button { background: none; border: none; color: #94a3b8; font-size: 16px; padding: 10px; cursor: pointer; }
    .nav button.active { color: #f59e0b; border-bottom: 2px solid #f59e0b; font-weight: bold; }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .card { background: #1e293b; padding: 20px; border-radius: 8px; margin-bottom: 16px; border: 1px solid #334155; }
    .box { background: rgba(15, 23, 42, 0.6); border-left: 4px solid #f59e0b; padding: 12px; margin-top: 10px; }
    .blue { border-color: #38bdf8; }
    .green { border-color: #34d399; }
    label { display: block; margin: 8px 0 4px; color: #94a3b8; }
    select, input { background: #334155; color: #fff; border: 1px solid #475569; padding: 8px; border-radius: 4px; width: 100%; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  </style>
</head>
<body>
<div class="container">
  <h2>Astrology Narrative & Ashtakavarga Engine</h2>
  <div class="nav">
    <button class="active" onclick="showTab('dasha')">Dasha Narrative</button>
    <button onclick="showTab('ashtaka')">Ashtakavarga Engine</button>
  </div>

  <div id="dasha" class="tab-content active">
    <div class="grid">
      <div class="card">
        <label>Mahadasha</label>
        <select id="maha" onchange="runDasha()">
          <option>Sun</option><option>Moon</option><option>Mars</option>
          <option selected>Rahu</option><option>Jupiter</option><option>Saturn</option>
          <option>Mercury</option><option>Ketu</option><option>Venus</option>
        </select>
        <label>Antardasha</label>
        <select id="antar" onchange="runDasha()">
          <option>Sun</option><option>Moon</option><option>Mars</option>
          <option>Rahu</option><option selected>Jupiter</option><option>Saturn</option>
          <option>Mercury</option><option>Ketu</option><option>Venus</option>
        </select>
        <label>Mutual Placement Axis</label>
        <select id="rel" onchange="runDasha()">
          <option value="1_7">1/7 Axis</option>
          <option value="3_11" selected>3/11 Axis</option>
          <option value="4_10">4/10 Axis</option>
          <option value="5_9">5/9 Axis</option>
          <option value="2_12">2/12 Axis</option>
          <option value="6_8">6/8 Axis</option>
        </select>
      </div>
      <div class="card">
        <h3>Interplay Summary</h3>
        <p id="summary">--</p>
        <div class="box blue" id="maha_out"></div>
        <div class="box green" id="antar_out"></div>
        <div class="box" id="rel_out"></div>
      </div>
    </div>
  </div>

  <div id="ashtaka" class="tab-content">
    <div class="grid">
      <div class="card">
        <h3>Career Metrics</h3>
        <label>10th House SAV: <input type="number" id="sav10" value="32" onchange="runAshtaka()"></label>
        <label>11th House SAV: <input type="number" id="sav11" value="34" onchange="runAshtaka()"></label>
        <label>12th House SAV: <input type="number" id="sav12" value="22" onchange="runAshtaka()"></label>
        <label>Saturn BAV: <input type="number" id="bav_sat" value="5" onchange="runAshtaka()"></label>
        <label>Sun BAV: <input type="number" id="bav_sun" value="4" onchange="runAshtaka()"></label>
        <div class="box blue" id="career_narrative"></div>
      </div>
      <div class="card">
        <h3>Health Metrics</h3>
        <label>1st House SAV: <input type="number" id="sav1" value="30" onchange="runAshtaka()"></label>
        <label>6th House SAV: <input type="number" id="sav6" value="24" onchange="runAshtaka()"></label>
        <label>8th House SAV: <input type="number" id="sav8" value="21" onchange="runAshtaka()"></label>
        <label>Mars BAV: <input type="number" id="bav_mars" value="3" onchange="runAshtaka()"></label>
        <div class="box green" id="health_narrative"></div>
      </div>
    </div>
  </div>
</div>

<script>
  function showTab(id) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav button').forEach(el => el.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
  }

  async function runDasha() {
    const res = await fetch('/api/v1/dasha-narrative', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        mahadasha: document.getElementById('maha').value,
        antardasha: document.getElementById('antar').value,
        relationship: document.getElementById('rel').value
      })
    });
    const data = await res.json();
    document.getElementById('summary').innerText = data.summary;
    document.getElementById('maha_out').innerText = data.mahadasha_narrative;
    document.getElementById('antar_out').innerText = data.antardasha_narrative;
    document.getElementById('rel_out').innerText = data.relationship_narrative;
  }

  async function runAshtaka() {
    const res = await fetch('/api/v1/ashtakavarga-eval', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        sav_10: document.getElementById('sav10').value,
        sav_11: document.getElementById('sav11').value,
        sav_12: document.getElementById('sav12').value,
        bav_saturn: document.getElementById('bav_sat').value,
        bav_sun: document.getElementById('bav_sun').value,
        sav_1: document.getElementById('sav1').value,
        sav_6: document.getElementById('sav6').value,
        sav_8: document.getElementById('sav8').value,
        bav_mars: document.getElementById('bav_mars').value
      })
    });
    const data = await res.json();
    document.getElementById('career_narrative').innerText = data.career.narrative;
    document.getElementById('health_narrative').innerText = data.health.narrative;
  }

  runDasha();
  runAshtaka();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

if __name__ == '__main__':
    print("Starting Astrology Engine API & Dashboard at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)