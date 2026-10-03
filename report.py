"""Standalone HTML report (the "Download report" button)."""
import html

import markdown
import plotly.graph_objects as go
import plotly.io as pio


def _fig(fig, first):
    fig = go.Figure(fig)  # copy so the on-screen figure keeps the Streamlit theme
    fig.update_layout(template="plotly_dark", paper_bgcolor="#1e2130", plot_bgcolor="#1e2130")
    return pio.to_html(fig, include_plotlyjs="cdn" if first else False, full_html=False,
                       config={"responsive": True, "displaylogo": False})


def build_report(title, subtitle, metrics, sections, figures):
    """metrics: [(label, value)], sections: [(heading, markdown)], figures: [plotly Figure]."""
    metric_html = "".join(
        f'<div class="metric"><div class="label">{html.escape(l)}</div><div class="val">{html.escape(str(v))}</div></div>'
        for l, v in metrics)
    section_html = "".join(
        f'<div class="card"><h2>{html.escape(h)}</h2>{markdown.markdown(body)}</div>' for h, body in sections)
    figure_html = "".join(f'<div class="card">{_fig(f, i == 0)}</div>' for i, f in enumerate(figures))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background:#0e1117; color:#e0e0e0;
         margin:0 auto; padding:30px; max-width:1200px; line-height:1.5; }}
  h1, h2 {{ color:#4A90E2; }}
  .sub {{ color:#9aa4b2; margin-top:-8px; }}
  .metrics {{ display:flex; flex-wrap:wrap; gap:12px; margin:20px 0; }}
  .metric {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:12px 16px; flex:1 1 150px; }}
  .metric .label {{ color:#9aa4b2; font-size:13px; }}
  .metric .val {{ color:#50E3C2; font-size:20px; font-weight:600; }}
  .card {{ background:#1e2130; border:1px solid #30363d; border-radius:10px; padding:20px 24px; margin-bottom:20px; }}
  @media (max-width:600px) {{ body {{ padding:16px; }} }}
</style>
</head>
<body>
<h1>🔮 {html.escape(title)}</h1>
<p class="sub">{html.escape(subtitle)}</p>
<div class="metrics">{metric_html}</div>
{section_html}
{figure_html}
</body>
</html>"""
