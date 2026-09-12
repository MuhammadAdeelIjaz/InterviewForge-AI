"""Visual theme for InterviewForge AI — a bright, high-contrast ironworks
motif (warm paper background, dark ink text, ember/gold accents).

Palette:
  paper     #FBF7F1   page background (warm off-white)
  panel     #FFFFFF   card / sidebar background
  line      #E7DCC9   borders
  ink-900   #241C15   primary text (near-black, warm)
  ink-600   #6E6255   secondary / muted text
  ember     #E8622C   primary accent (hot metal)
  ember-dk  #B8481C   accent text on light backgrounds (better contrast)
  gold      #C9891B   secondary accent, tuned darker for legibility on white
  good/warn/bad        semantic colors for score bands, tuned for light bg —
                       a text label always sits next to the color so a
                       reading is never conveyed by color alone
Typography: Space Grotesk for headings (geometric, industrial),
IBM Plex Sans for body copy — a deliberate pairing, not the default
Streamlit sans-serif.
"""

# Icon shown next to each pipeline stage — sidebar stepper + page headers.
STEP_ICONS = [
    "🗂️",  # Setup
    "🪪",  # Candidate & Job Profiles
    "🔍",  # Information Check
    "🎯",  # Job Match Analysis
    "🧯",  # Interview Risk Engine
    "❓",  # Question Engine
    "📶",  # Question Priority
    "🧭",  # Answer Blueprint
    "🥊",  # Tough Question Coach
    "🛡️",  # Battle Plan & Forge Score
    "🔁",  # Practice & Refine Loop
]

FORGE_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">

<style>
:root {
  --paper: #FBF7F1;
  --panel: #FFFFFF;
  --line: #E7DCC9;
  --ink-900: #241C15;
  --ink-600: #6E6255;
  --ember: #E8622C;
  --ember-dk: #B8481C;
  --gold: #C9891B;
  --good: #2E8B57;
  --warn: #B9800E;
  --bad: #C0392B;
}

html, body, [class*="css"]  {
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 16px;
}

.stApp {
  background:
    radial-gradient(ellipse 900px 500px at 15% -10%, rgba(232,98,44,0.07), transparent 60%),
    radial-gradient(ellipse 700px 500px at 100% 0%, rgba(201,137,27,0.06), transparent 55%),
    var(--paper);
  color: var(--ink-900);
}

h1, h2, h3, h4 {
  font-family: 'Space Grotesk', sans-serif !important;
  color: var(--ink-900) !important;
  letter-spacing: -0.01em;
}
h3 { display: flex; align-items: center; gap: 10px; }

p, li, span, label, div { line-height: 1.55; color: var(--ink-900); }

/* ---------------------------------------------------------------- */
/* Hero title bar                                                    */
/* ---------------------------------------------------------------- */
.forge-hero {
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 2px solid var(--line);
  padding-bottom: 18px;
  margin-bottom: 4px;
}
.forge-hero .anvil {
  font-size: 2.3rem;
  line-height: 1;
}
.forge-hero h1 {
  font-size: 2.1rem !important;
  margin: 0 !important;
  background: linear-gradient(90deg, var(--ink-900) 15%, var(--ember) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.forge-tagline {
  color: var(--ink-600);
  font-size: 0.97rem;
  margin-top: -6px;
  margin-bottom: 14px;
}

/* Progress readout under the hero */
.forge-progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.82rem;
  color: var(--ink-600);
  margin-bottom: 4px;
}
.forge-progress-label b { color: var(--ember-dk); font-family: 'Space Grotesk', sans-serif; }
div[data-testid="stProgress"] > div > div {
  background-color: var(--line) !important;
}
div[data-testid="stProgress"] > div > div > div {
  background-image: linear-gradient(90deg, var(--ember), var(--gold)) !important;
}

/* ---------------------------------------------------------------- */
/* Stage stepper (sidebar)                                           */
/* ---------------------------------------------------------------- */
.stage-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 9px;
  margin-bottom: 3px;
  font-size: 0.9rem;
  transition: background 0.15s ease;
}
.stage-item .icon { font-size: 1.0rem; width: 20px; text-align: center; flex-shrink: 0; }
.stage-item .num {
  width: 20px; height: 20px;
  border-radius: 5px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem;
  font-family: 'Space Grotesk', sans-serif;
  flex-shrink: 0;
}
.stage-current { background: rgba(232,98,44,0.12); border: 1px solid rgba(232,98,44,0.30); }
.stage-current .num { background: var(--ember); color: #FFFFFF; font-weight: 700; }
.stage-current span.label { color: var(--ink-900); font-weight: 600; }
.stage-done .num { background: #FFF3E6; color: var(--gold); border: 1px solid var(--gold); }
.stage-done span.label { color: var(--ink-600); }
.stage-todo .num { background: var(--line); color: var(--ink-600); }
.stage-todo span.label { color: var(--ink-600); }

/* ---------------------------------------------------------------- */
/* Cards                                                             */
/* ---------------------------------------------------------------- */
.forge-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-left: 4px solid var(--ember);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 14px;
  box-shadow: 0 1px 3px rgba(36,28,21,0.06);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.forge-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(36,28,21,0.10);
}
.forge-card h4 {
  margin-top: 0 !important;
  font-size: 1.05rem !important;
  display: flex; align-items: center; flex-wrap: wrap; gap: 6px;
}
.forge-card p, .forge-card li { color: var(--ink-900); }
.forge-card b, .forge-card strong { color: var(--ember-dk); font-weight: 600; }
.forge-card em { color: var(--ink-600); }
.forge-card ul { margin: 4px 0 10px 0; padding-left: 20px; }
.forge-card.gold { border-left-color: var(--gold); }
.forge-card.slate { border-left-color: var(--ink-600); }
.forge-card.good { border-left-color: var(--good); }
.forge-card.bad { border-left-color: var(--bad); }

/* ---------------------------------------------------------------- */
/* Priority chips                                                    */
/* ---------------------------------------------------------------- */
.chip {
  display: inline-block;
  font-size: 0.72rem;
  font-family: 'Space Grotesk', sans-serif;
  padding: 2px 10px;
  border-radius: 20px;
  font-weight: 600;
  margin-left: 8px;
  vertical-align: middle;
}
.chip-high { background: #FDEBE1; color: var(--ember-dk); border: 1px solid var(--ember-dk); }
.chip-medium { background: #FBF0DA; color: var(--gold); border: 1px solid var(--gold); }
.chip-low { background: #EFEBE5; color: var(--ink-600); border: 1px solid var(--ink-600); }

/* ---------------------------------------------------------------- */
/* Score blocks                                                      */
/* ---------------------------------------------------------------- */
.score-block {
  text-align: center;
  background: var(--panel);
  border: 1px solid var(--line);
  border-top: 4px solid var(--ink-600);
  border-radius: 14px;
  padding: 20px 10px 16px;
  box-shadow: 0 1px 3px rgba(36,28,21,0.06);
  transition: transform 0.15s ease;
}
.score-block:hover { transform: translateY(-2px); }
.score-block .num {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2.3rem;
  font-weight: 700;
}
.score-block .band {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 2px;
}
.score-block .label {
  font-size: 0.8rem;
  color: var(--ink-600);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-top: 6px;
}

/* ---------------------------------------------------------------- */
/* Buttons                                                           */
/* ---------------------------------------------------------------- */
div.stButton > button, div.stDownloadButton > button {
  background: var(--ember);
  color: #FFFFFF;
  border: none;
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 600;
  border-radius: 22px;
  padding: 0.55em 1.3em;
  box-shadow: 0 2px 8px rgba(232,98,44,0.30);
  transition: transform 0.12s ease, background 0.12s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
  background: var(--ember-dk);
  color: #FFFFFF;
  transform: translateY(-1px);
}
div.stButton > button:disabled {
  background: var(--line);
  color: var(--ink-600);
  box-shadow: none;
}

/* ---------------------------------------------------------------- */
/* Tabs, expanders, inputs                                           */
/* ---------------------------------------------------------------- */
button[data-baseweb="tab"] {
  font-family: 'Space Grotesk', sans-serif;
  color: var(--ink-600) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--ember-dk) !important;
  border-bottom-color: var(--ember) !important;
}
div[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius: 10px !important;
  background: var(--panel);
}
input, textarea {
  background-color: var(--panel) !important;
  color: var(--ink-900) !important;
  border-color: var(--line) !important;
}

section[data-testid="stSidebar"] {
  background: #F5EEE2;
  border-right: 1px solid var(--line);
}

hr { border-color: var(--line) !important; }

/* Small helper text under section headers */
.forge-caption { color: var(--ink-600); font-size: 0.88rem; margin-top: -8px; }
</style>
"""


def hero_html(title="InterviewForge AI", tagline="Forge a sharper interview, one stage at a time."):
    return f"""
<div class="forge-hero">
  <div class="anvil">🔥</div>
  <h1>{title}</h1>
</div>
<div class="forge-tagline">{tagline}</div>
"""


def progress_label_html(step_index, total, step_name):
    pct = int(round((step_index) / (total - 1) * 100)) if total > 1 else 0
    return (
        f'<div class="forge-progress-label">'
        f'<span>Stage <b>{step_index + 1}</b> of {total} &middot; {step_name}</span>'
        f'<span>{pct}% through the pipeline</span></div>'
    )


def stage_sidebar_html(steps, icons, current_index):
    rows = []
    for i, name in enumerate(steps):
        icon = icons[i] if i < len(icons) else "•"
        if i < current_index:
            cls, mark = "stage-done", "✓"
        elif i == current_index:
            cls, mark = "stage-current", str(i + 1)
        else:
            cls, mark = "stage-todo", str(i + 1)
        rows.append(
            f'<div class="stage-item {cls}"><div class="num">{mark}</div>'
            f'<div class="icon">{icon}</div>'
            f'<span class="label">{name}</span></div>'
        )
    return "<div>" + "".join(rows) + "</div>"


def chip(priority):
    p = (priority or "").lower()
    cls = "chip-high" if p == "high" else "chip-medium" if p == "medium" else "chip-low"
    return f'<span class="chip {cls}">{priority}</span>'


def score_band(value):
    """Return (band_label, color) for a 0-100 score."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—", "var(--ink-600)"
    if v >= 75:
        return "Strong", "var(--good)"
    if v >= 50:
        return "Developing", "var(--warn)"
    return "Needs work", "var(--bad)"


def score_block_html(value, label):
    band, color = score_band(value)
    display_val = value if value is not None else "—"
    return (
        f'<div class="score-block" style="border-top-color:{color}">'
        f'<div class="num" style="color:{color}">{display_val}</div>'
        f'<div class="band" style="color:{color}">{band}</div>'
        f'<div class="label">{label}</div></div>'
    )
