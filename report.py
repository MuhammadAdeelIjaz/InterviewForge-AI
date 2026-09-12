"""Compile everything the session produced into one downloadable Markdown
report — the candidate's personal Interview Battle Plan."""


def _bullets(items):
    if not items:
        return "_None noted._\n"
    return "\n".join(f"- {i}" for i in items) + "\n"


def compile_report(data):
    cp = data.get("candidate_profile", {}) or {}
    jp = data.get("job_profile", {}) or {}
    match = data.get("match_analysis", {}) or {}
    risk = data.get("risk_engine", {}) or {}
    battle = data.get("battle_plan", {}) or {}
    score = data.get("forge_score", {}) or {}
    blueprints = data.get("blueprints", {}) or {}
    tough = data.get("tough_coaching", {}) or {}
    questions = data.get("questions", {}) or {}
    priorities = data.get("priorities", {}) or {}

    lines = []
    lines.append(f"# InterviewForge Battle Plan")
    lines.append(f"**Candidate:** {cp.get('name', 'N/A')}  ")
    lines.append(f"**Target role:** {jp.get('role_title', 'N/A')} at {jp.get('company', 'N/A')}\n")

    lines.append("## Forge Score")
    lines.append(f"- **Overall Forge Score:** {score.get('forge_score', '—')}/100")
    lines.append(f"- **Job Fit:** {score.get('job_fit', '—')}/100")
    lines.append(f"- **Technical Readiness:** {score.get('technical_readiness', '—')}/100")
    lines.append(f"- **Behavioral Readiness:** {score.get('behavioral_readiness', '—')}/100\n")

    lines.append("### Top Improvement Areas")
    for area in score.get("top_improvement_areas", []) or []:
        lines.append(f"- **{area.get('area')}** — {area.get('action')}")
    lines.append("")

    lines.append("## Job Match Analysis")
    lines.append(f"**Match score:** {match.get('match_score', '—')}/100\n")
    lines.append(f"{match.get('summary', '')}\n")
    lines.append("**Strengths**")
    lines.append(_bullets(match.get("strengths")))
    lines.append("**Gaps**")
    lines.append(_bullets(match.get("gaps")))

    swot = risk.get("swot", {})
    lines.append("## SWOT")
    for label in ["strengths", "weaknesses", "opportunities", "threats"]:
        lines.append(f"**{label.title()}**")
        lines.append(_bullets(swot.get(label)))

    pitch = risk.get("pitch", {})
    lines.append("## Elevator Pitches")
    lines.append(f"**30-second pitch:** {pitch.get('pitch_30s', '')}\n")
    lines.append(f"**60-second pitch:** {pitch.get('pitch_60s', '')}\n")
    lines.append(f"**HR framing:** {pitch.get('pitch_hr_angle', '')}\n")
    lines.append(f"**Technical framing:** {pitch.get('pitch_tech_angle', '')}\n")

    lines.append("## Risk Areas")
    for r in risk.get("risk_areas", []) or []:
        lines.append(f"- **{r.get('area')}** — {r.get('why_risky')} _Mitigation:_ {r.get('mitigation')}")
    lines.append("")

    lines.append("## Interview Battle Plan")
    for phase in battle.get("battle_plan", []) or []:
        lines.append(f"### {phase.get('phase')}")
        lines.append(_bullets(phase.get("actions")))
    lines.append("**Key talking points**")
    lines.append(_bullets(battle.get("key_talking_points")))

    lines.append("## Question Bank & Answer Blueprints")
    prio_map = {p["id"]: p["priority"] for p in priorities.get("priorities", [])} if priorities else {}
    bp_map = {b["id"]: b for b in blueprints.get("blueprints", [])} if blueprints else {}
    for category, qs in (questions or {}).items():
        if not qs:
            continue
        lines.append(f"### {category}")
        for q in qs:
            qid = q.get("id")
            pr = prio_map.get(qid, "")
            lines.append(f"**Q ({pr}):** {q.get('question')}")
            bp = bp_map.get(qid)
            if bp:
                lines.append(f"- Why asked: {bp.get('why_asked')}")
                lines.append(f"- What to show: {', '.join(bp.get('what_to_show') or [])}")
                lines.append(f"- CV evidence: {', '.join(bp.get('cv_evidence') or [])}")
                lines.append(f"- Outline: {bp.get('answer_outline')}")
            tc = tough.get(qid)
            if tc:
                lines.append(f"- Tough-question trap: {tc.get('common_trap')}")
                lines.append(f"- Model answer: {tc.get('strong_sample_answer')}")
            lines.append("")

    return "\n".join(lines)
