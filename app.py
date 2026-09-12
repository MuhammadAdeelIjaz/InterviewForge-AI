"""
InterviewForge AI
==================
A free, no-RAG interview-prep pipeline built on Streamlit + Groq.

Every stage below makes a single direct call to an LLM with the relevant
context stuffed into the prompt — there is no document store, no
embeddings, and no retrieval step anywhere in this app.
"""
import json

import streamlit as st

import engine
from engine import ForgeError
import file_utils
import styles
import report as report_mod

# --------------------------------------------------------------------------
# Page config & theme
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="InterviewForge AI",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(styles.FORGE_CSS, unsafe_allow_html=True)

STEPS = [
    "Setup",
    "Candidate & Job Profiles",
    "Information Check",
    "Job Match Analysis",
    "Interview Risk Engine",
    "Question Engine",
    "Question Priority",
    "Answer Blueprint",
    "Tough Question Coach",
    "Battle Plan & Forge Score",
    "Practice & Refine Loop",
]

# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "max_step" not in st.session_state:
    st.session_state.max_step = 0
if "data" not in st.session_state:
    st.session_state.data = {}
if "model" not in st.session_state:
    st.session_state.model = engine.DEFAULT_MODEL

data = st.session_state.data


def goto(i):
    st.session_state.step = i
    st.session_state.max_step = max(st.session_state.max_step, i)


def safe_call(label, fn, *args, **kwargs):
    """Run an engine call with a spinner and friendly error handling."""
    try:
        with st.spinner(label):
            return fn(*args, **kwargs)
    except ForgeError as e:
        st.error(str(e))
        return None
    except Exception as e:  # noqa: BLE001
        st.error(f"Unexpected error: {e}")
        return None


def card(title, body_html, tone=""):
    cls = f"forge-card {tone}".strip()
    st.markdown(f'<div class="{cls}"><h4>{title}</h4>{body_html}</div>',
                unsafe_allow_html=True)


def bullet_html(items):
    if not items:
        return "<p style='color:#8B9491'>None noted.</p>"
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔥 InterviewForge AI")
    st.caption("No RAG. Just fast, direct LLM calls on Groq's free tier.")
    st.divider()

    st.markdown(styles.stage_sidebar_html(STEPS, styles.STEP_ICONS, st.session_state.step),
                unsafe_allow_html=True)

    reachable = [s for i, s in enumerate(STEPS) if i <= st.session_state.max_step]
    if len(reachable) > 1:
        jump = st.selectbox("Jump to a completed step", reachable,
                             index=reachable.index(STEPS[st.session_state.step]))
        if STEPS.index(jump) != st.session_state.step:
            goto(STEPS.index(jump))
            st.rerun()

    st.divider()
    st.markdown("**Engine settings**")
    st.session_state.model = st.selectbox(
        "Groq model",
        [engine.DEFAULT_MODEL, engine.FAST_MODEL],
        format_func=lambda m: "GPT-OSS 120B (quality)" if "120b" in m
        else "GPT-OSS 20B (fast)",
    )
    api_key = engine.get_api_key()
    if api_key:
        st.success("Groq API key loaded from secrets.")
    else:
        st.error(
            "No Groq API key found in secrets. Add `GROQ_API_KEY` to "
            "`.streamlit/secrets.toml` locally, or to your app's Secrets "
            "in Streamlit Community Cloud, then reload."
        )

    st.divider()
    if st.button("↺ Reset entire session"):
        st.session_state.clear()
        st.rerun()

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.markdown(styles.hero_html(), unsafe_allow_html=True)

step = st.session_state.step
st.markdown(styles.progress_label_html(step, len(STEPS), STEPS[step]),
            unsafe_allow_html=True)
st.progress(step / (len(STEPS) - 1) if len(STEPS) > 1 else 0.0)
st.write("")

# ==========================================================================
# STEP 0 — Setup
# ==========================================================================
if step == 0:
    st.subheader(f"{styles.STEP_ICONS[0]} 1 · Feed the forge")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Candidate CV**")
        cv_file = st.file_uploader("Upload CV (PDF, DOCX, or TXT)",
                                    type=["pdf", "docx", "txt"])
        cv_pasted = st.text_area("...or paste CV text here", height=180,
                                  placeholder="Paste resume text if you'd "
                                              "rather not upload a file.")
    with col2:
        st.markdown("**Target role**")
        company_name = st.text_input("Company (optional)")
        jd_pasted = st.text_area("Paste the job description", height=220,
                                  placeholder="Paste the full job posting "
                                              "text here.")

    st.write("")
    disabled = not (jd_pasted and (cv_file or cv_pasted))
    if st.button("🔥 Forge my profile", disabled=disabled, type="primary"):
        cv_text = file_utils.extract_text_from_upload(cv_file) if cv_file else cv_pasted
        result = safe_call("Reading your CV and the job description…",
                            engine.extract_profiles, cv_text, jd_pasted, company_name)
        if result:
            data["cv_text"] = cv_text
            data["jd_text"] = jd_pasted
            data["company_name"] = company_name
            data["candidate_profile"] = result.get("candidate_profile", {})
            data["job_profile"] = result.get("job_profile", {})
            goto(1)
            st.rerun()
    if disabled:
        st.caption("Add a CV (upload or paste) and a job description to continue.")

# ==========================================================================
# STEP 1 — Profiles
# ==========================================================================
elif step == 1:
    st.subheader(f"{styles.STEP_ICONS[1]} 2 · Candidate & job profiles")
    cp, jp = data.get("candidate_profile", {}), data.get("job_profile", {})
    col1, col2 = st.columns(2)

    with col1:
        card(cp.get("name", "Candidate"),
             f"<p><em>{cp.get('headline','')}</em></p>"
             f"<p><b>Experience:</b> {cp.get('years_experience','—')}</p>"
             f"<p><b>Top skills:</b></p>{bullet_html(cp.get('top_skills'))}"
             f"<p><b>Key achievements:</b></p>{bullet_html(cp.get('key_achievements'))}")
        with st.expander("Employment history"):
            for job in cp.get("employment_history", []) or []:
                st.markdown(f"**{job.get('title','')}** — {job.get('company','')} "
                            f"({job.get('duration','')})")
                for h in job.get("highlights", []) or []:
                    st.markdown(f"- {h}")
        with st.expander("Education, certifications & flags"):
            st.markdown("**Education**")
            st.markdown(bullet_html(cp.get("education")), unsafe_allow_html=True)
            st.markdown("**Certifications**")
            st.markdown(bullet_html(cp.get("certifications")), unsafe_allow_html=True)
            st.markdown("**Potential gaps / flags**")
            st.markdown(bullet_html(cp.get("potential_gaps_or_flags")), unsafe_allow_html=True)

    with col2:
        card(f"{jp.get('role_title','Role')} @ {jp.get('company','—')}",
             f"<p><b>Seniority:</b> {jp.get('seniority','—')}</p>"
             f"<p><b>Must-have skills:</b></p>{bullet_html(jp.get('must_have_skills'))}"
             f"<p><b>Nice-to-have skills:</b></p>{bullet_html(jp.get('nice_to_have_skills'))}",
             tone="gold")
        with st.expander("Responsibilities & culture signals"):
            st.markdown("**Core responsibilities**")
            st.markdown(bullet_html(jp.get("core_responsibilities")), unsafe_allow_html=True)
            st.markdown("**Culture / values signals**")
            st.markdown(bullet_html(jp.get("culture_or_values_signals")), unsafe_allow_html=True)
            st.markdown("**Keywords**")
            st.markdown(bullet_html(jp.get("keywords")), unsafe_allow_html=True)

    st.write("")
    if st.button("Run information check →", type="primary"):
        result = safe_call("Checking whether we have enough to work with…",
                            engine.check_information_sufficiency, cp, jp)
        if result:
            data["info_check"] = result
            goto(2)
            st.rerun()

# ==========================================================================
# STEP 2 — Information check
# ==========================================================================
elif step == 2:
    st.subheader(f"{styles.STEP_ICONS[2]} 3 · Information check")
    info = data.get("info_check", {})
    status = info.get("status", "sufficient")

    if status == "sufficient":
        st.success("The profile has enough detail to build a strong strategy.")
        if st.button("Continue to job match analysis →", type="primary"):
            goto(3)
            st.rerun()
    else:
        card("A few gaps could sharpen your prep",
             bullet_html(info.get("missing_points")))
        st.markdown("**Answer what you can — skip anything you'd rather not.**")
        qs = info.get("followup_questions", [])
        answers = {}
        with st.form("followup_form"):
            for q in qs:
                answers[q["id"]] = st.text_input(q["question"], key=f"fu_{q['id']}",
                                                  help=q.get("why_it_matters", ""))
            submitted = st.form_submit_button("Submit answers", type="primary")
        if submitted:
            qa_pairs = [{"question": q["question"], "answer": answers.get(q["id"], "")}
                        for q in qs if answers.get(q["id"])]
            if qa_pairs:
                updated = safe_call("Updating your profile…",
                                     engine.apply_followup_answers,
                                     data["candidate_profile"], data["job_profile"], qa_pairs)
                if updated:
                    data["candidate_profile"] = updated
            goto(3)
            st.rerun()
        st.write("")
        if st.button("Skip this and continue anyway"):
            goto(3)
            st.rerun()

# ==========================================================================
# STEP 3 — Job match analysis
# ==========================================================================
elif step == 3:
    st.subheader(f"{styles.STEP_ICONS[3]} 4 · Job match analysis")
    if "match_analysis" not in data:
        result = safe_call("Scoring the match…", engine.job_match_analysis,
                            data["candidate_profile"], data["job_profile"])
        if result:
            data["match_analysis"] = result
        else:
            st.stop()
    match = data["match_analysis"]

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(styles.score_block_html(match.get("match_score"), "Match score"),
                    unsafe_allow_html=True)
    with col2:
        st.markdown(f"_{match.get('summary','')}_")

    c1, c2 = st.columns(2)
    with c1:
        card("Strengths", bullet_html(match.get("strengths")))
    with c2:
        card("Gaps", bullet_html(match.get("gaps")), tone="slate")

    if st.button("Run interview risk engine →", type="primary"):
        goto(4)
        st.rerun()

# ==========================================================================
# STEP 4 — Interview risk engine
# ==========================================================================
elif step == 4:
    st.subheader(f"{styles.STEP_ICONS[4]} 5 · Interview risk engine")
    if "risk_engine" not in data:
        result = safe_call("Building your SWOT, pitches, and risk map…",
                            engine.interview_risk_engine, data["candidate_profile"],
                            data["job_profile"], data["match_analysis"])
        if result:
            data["risk_engine"] = result
        else:
            st.stop()
    risk = data["risk_engine"]
    swot = risk.get("swot", {})

    st.markdown("**SWOT analysis**")
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        card("Strengths", bullet_html(swot.get("strengths")))
        card("Opportunities", bullet_html(swot.get("opportunities")), tone="gold")
    with r1c2:
        card("Weaknesses", bullet_html(swot.get("weaknesses")), tone="slate")
        card("Threats", bullet_html(swot.get("threats")), tone="slate")

    st.markdown("**Elevator pitches**")
    pitch = risk.get("pitch", {})
    p1, p2 = st.columns(2)
    with p1:
        card("30-second pitch", f"<p>{pitch.get('pitch_30s','')}</p>")
        card("Angle for HR / recruiter", f"<p>{pitch.get('pitch_hr_angle','')}</p>", tone="gold")
    with p2:
        card("60-second pitch", f"<p>{pitch.get('pitch_60s','')}</p>")
        card("Angle for technical interviewer", f"<p>{pitch.get('pitch_tech_angle','')}</p>", tone="gold")

    st.markdown("**Risk areas**")
    for r in risk.get("risk_areas", []) or []:
        card(r.get("area", "Risk"),
             f"<p>{r.get('why_risky','')}</p><p><b>Mitigation:</b> {r.get('mitigation','')}</p>",
             tone="slate")

    if st.button("Generate interview questions →", type="primary"):
        goto(5)
        st.rerun()

# ==========================================================================
# STEP 5 — Question engine
# ==========================================================================
elif step == 5:
    st.subheader(f"{styles.STEP_ICONS[5]} 6 · Question engine")
    if "questions" not in data:
        result = safe_call("Drafting realistic interview questions…",
                            engine.generate_questions, data["candidate_profile"],
                            data["job_profile"], data["risk_engine"])
        if result:
            data["questions"] = result
        else:
            st.stop()
    questions = data["questions"]

    tabs = st.tabs(list(questions.keys()))
    for tab, category in zip(tabs, questions.keys()):
        with tab:
            for q in questions[category]:
                st.markdown(f"- {q['question']}")

    if st.button("Prioritize these questions →", type="primary"):
        goto(6)
        st.rerun()

# ==========================================================================
# STEP 6 — Question priority
# ==========================================================================
elif step == 6:
    st.subheader(f"{styles.STEP_ICONS[6]} 7 · Question priority")
    if "priorities" not in data:
        flat = [{"id": q["id"], "category": cat, "question": q["question"]}
                for cat, qs in data["questions"].items() for q in qs]
        data["_flat_questions"] = flat
        result = safe_call("Triaging by likelihood and importance…",
                            engine.prioritize_questions, flat)
        if result:
            data["priorities"] = result
        else:
            st.stop()

    prio_map = {p["id"]: p["priority"] for p in data["priorities"].get("priorities", [])}
    flat = data.get("_flat_questions") or [
        {"id": q["id"], "category": cat, "question": q["question"]}
        for cat, qs in data["questions"].items() for q in qs
    ]

    cols = st.columns(3)
    for col, level in zip(cols, ["High", "Medium", "Low"]):
        with col:
            st.markdown(f"**{level} priority**")
            items = [f for f in flat if prio_map.get(f["id"]) == level]
            if not items:
                st.caption("None")
            for it in items:
                st.markdown(f"- _{it['category']}_: {it['question']}")

    if st.button("Build answer blueprints →", type="primary"):
        goto(7)
        st.rerun()

# ==========================================================================
# STEP 7 — Answer blueprint
# ==========================================================================
elif step == 7:
    st.subheader(f"{styles.STEP_ICONS[7]} 8 · Answer blueprint")
    prio_map = {p["id"]: p["priority"] for p in data["priorities"].get("priorities", [])}
    flat = data.get("_flat_questions", [])
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    ranked = sorted(flat, key=lambda f: priority_order.get(prio_map.get(f["id"]), 3))
    top_batch = ranked[:10]

    if "blueprints" not in data:
        result = safe_call("Building answer blueprints for your top questions…",
                            engine.build_answer_blueprints, top_batch,
                            data["candidate_profile"], data["job_profile"])
        if result:
            data["blueprints"] = result
        else:
            st.stop()

    bp_map = {b["id"]: b for b in data["blueprints"].get("blueprints", [])}
    for f in top_batch:
        bp = bp_map.get(f["id"])
        if not bp:
            continue
        chip = styles.chip(prio_map.get(f["id"], ""))
        card(f"{f['question']} {chip}",
             f"<p><b>Why asked:</b> {bp.get('why_asked','')}</p>"
             f"<p><b>What to show:</b></p>{bullet_html(bp.get('what_to_show'))}"
             f"<p><b>CV evidence to cite:</b></p>{bullet_html(bp.get('cv_evidence'))}"
             f"<p><b>Answer outline:</b> {bp.get('answer_outline','')}</p>")

    st.caption(f"Blueprints built for the top {len(top_batch)} questions by priority "
               f"(out of {len(flat)} total) to keep API usage light on the free tier.")

    if st.button("Go to Tough Question Coach →", type="primary"):
        goto(8)
        st.rerun()

# ==========================================================================
# STEP 8 — Tough question coach
# ==========================================================================
elif step == 8:
    st.subheader(f"{styles.STEP_ICONS[8]} 9 · Tough question coach")
    flat = data.get("_flat_questions", [])
    bp_map = {b["id"]: b for b in data.get("blueprints", {}).get("blueprints", [])}
    coachable = [f for f in flat if f["id"] in bp_map]

    if "tough_coaching" not in data:
        data["tough_coaching"] = {}

    options = {f"{f['category']}: {f['question']}": f for f in coachable}
    choice = st.selectbox("Pick a question to pressure-test", list(options.keys()))
    if st.button("Get tough-question coaching"):
        f = options[choice]
        result = safe_call("Pressure-testing this answer…", engine.tough_question_coach,
                            f["question"], data["candidate_profile"], bp_map[f["id"]])
        if result:
            data["tough_coaching"][f["id"]] = result

    for f in coachable:
        coaching = data["tough_coaching"].get(f["id"])
        if coaching:
            card(f["question"],
                 f"<p><b>Why it's tough:</b> {coaching.get('why_this_is_tough','')}</p>"
                 f"<p><b>Common trap:</b> {coaching.get('common_trap','')}</p>"
                 f"<p><b>Coaching tips:</b></p>{bullet_html(coaching.get('coaching_tips'))}"
                 f"<p><b>Strong sample answer:</b> {coaching.get('strong_sample_answer','')}</p>",
                 tone="gold")

    st.write("")
    if st.button("Build my battle plan & forge score →", type="primary"):
        goto(9)
        st.rerun()

# ==========================================================================
# STEP 9 — Battle plan & Forge score
# ==========================================================================
elif step == 9:
    st.subheader(f"{styles.STEP_ICONS[9]} 10 · Battle plan & Forge Score")

    if "battle_plan" not in data:
        result = safe_call("Compiling your battle plan…", engine.build_battle_plan,
                            data["candidate_profile"], data["job_profile"],
                            data["match_analysis"], data["risk_engine"])
        if result:
            data["battle_plan"] = result
        else:
            st.stop()

    if "forge_score" not in data:
        summary = {k: v.get("why_asked") for k, v in
                   {b["id"]: b for b in data.get("blueprints", {}).get("blueprints", [])}.items()}
        result = safe_call("Calculating your Forge Score…", engine.compute_forge_score,
                            data["candidate_profile"], data["job_profile"],
                            data["match_analysis"], data["risk_engine"], summary)
        if result:
            data["forge_score"] = result
            if not data.get("_celebrated"):
                st.balloons()
                data["_celebrated"] = True
        else:
            st.stop()

    score = data["forge_score"]
    cols = st.columns(4)
    labels = [("forge_score", "Forge Score"), ("job_fit", "Job Fit"),
              ("technical_readiness", "Technical Readiness"),
              ("behavioral_readiness", "Behavioral Readiness")]
    for col, (key, label) in zip(cols, labels):
        with col:
            st.markdown(styles.score_block_html(score.get(key), label),
                        unsafe_allow_html=True)

    st.write("")
    card("Top improvement areas",
         "".join(f"<p><b>{a.get('area')}</b> — {a.get('action')}</p>"
                 for a in score.get("top_improvement_areas", [])) or "<p>None</p>",
         tone="gold")

    st.markdown("**Battle plan**")
    battle = data["battle_plan"]
    for phase in battle.get("battle_plan", []):
        card(phase.get("phase", ""), bullet_html(phase.get("actions")))
    card("Key talking points", bullet_html(battle.get("key_talking_points")), tone="gold")

    st.write("")
    if st.button("Go to practice & refine loop →", type="primary"):
        goto(10)
        st.rerun()

# ==========================================================================
# STEP 10 — Practice & refine loop
# ==========================================================================
elif step == 10:
    st.subheader(f"{styles.STEP_ICONS[10]} 11 · Practice & refine loop")
    st.caption("Answer a question out loud or in writing, get graded, then send "
               "weak spots straight back to your Answer Blueprint and Tough "
               "Question Coach.")

    flat = data.get("_flat_questions", [])
    bp_map = {b["id"]: b for b in data.get("blueprints", {}).get("blueprints", [])}
    practicable = [f for f in flat if f["id"] in bp_map]
    if "practice_history" not in data:
        data["practice_history"] = {}

    options = {f"{f['category']}: {f['question']}": f for f in practicable}
    if options:
        choice = st.selectbox("Choose a question to practice", list(options.keys()))
        f = options[choice]
        answer = st.text_area("Your answer", height=160, key=f"practice_{f['id']}")
        if st.button("Get feedback", type="primary") and answer.strip():
            result = safe_call("Grading your answer…", engine.practice_feedback,
                                f["question"], answer, bp_map[f["id"]],
                                data["candidate_profile"])
            if result:
                data["practice_history"][f["id"]] = {"answer": answer, "feedback": result}

        rec = data["practice_history"].get(f["id"])
        if rec:
            fb = rec["feedback"]
            card(f"Feedback — score {fb.get('score','—')}/100",
                 f"<p>{fb.get('feedback','')}</p>"
                 f"<p><b>Strengths:</b></p>{bullet_html(fb.get('strengths'))}"
                 f"<p><b>Improve:</b></p>{bullet_html(fb.get('improve'))}"
                 f"<p><b>Revised answer:</b> {fb.get('revised_answer','')}</p>")
            if st.button("↻ Send weak areas back to Tough Question Coach"):
                coaching = safe_call("Updating your coaching with this feedback…",
                                      engine.tough_question_coach, f["question"],
                                      data["candidate_profile"], bp_map[f["id"]])
                if coaching:
                    data.setdefault("tough_coaching", {})[f["id"]] = coaching
                    st.success("Updated. Head back to Tough Question Coach to review it.")
    else:
        st.info("Build some answer blueprints first (steps 8-9) to unlock practice mode.")

    st.divider()
    st.markdown("### Export")
    md_report = report_mod.compile_report(data)
    st.download_button("⬇ Download full Interview Battle Plan (Markdown)",
                        data=md_report, file_name="interviewforge_battle_plan.md",
                        mime="text/markdown", type="primary")

st.write("")
st.caption("InterviewForge AI — powered by Groq. No documents are stored; "
           "everything lives only in this browser session.")
