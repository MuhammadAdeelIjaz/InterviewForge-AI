"""
InterviewForge AI — Core Engine
--------------------------------
Every function here makes one direct call to Groq's chat completion API.
There is no vector store, no embeddings, and no retrieval step of any kind —
each call gets the full relevant context (CV text, job description, and the
outputs of earlier stages) stuffed directly into the prompt. That keeps the
app simple, fast, and free to run on Groq's free tier.
"""
import json
import os
import re
import time

import streamlit as st
from groq import Groq

DEFAULT_MODEL = "openai/gpt-oss-120b"
FAST_MODEL = "openai/gpt-oss-20b"


# --------------------------------------------------------------------------
# Low level client / call helpers
# --------------------------------------------------------------------------

def get_api_key():
    """Read the Groq API key from Streamlit secrets (or an environment
    variable for local dev without a secrets.toml). No key is ever taken
    from the UI or stored in session state."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY")


def get_client():
    api_key = get_api_key()
    if not api_key:
        return None
    return Groq(api_key=api_key)


def _strip_code_fence(text):
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip())
    text = re.sub(r"```$", "", text.strip())
    return text.strip()


def _extract_json(text):
    text = _strip_code_fence(text)
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None


class ForgeError(Exception):
    pass


def call_llm(system_prompt, user_prompt, json_mode=True, temperature=0.4,
             model=None, max_retries=3):
    client = get_client()
    if client is None:
        raise ForgeError(
            "No Groq API key configured. Add one in the sidebar, or set "
            "GROQ_API_KEY in Streamlit secrets / environment variables."
        )
    model = model or st.session_state.get("model", DEFAULT_MODEL)

    kwargs = dict(
        model=model,
        temperature=temperature,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_err = None
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content
            if json_mode:
                parsed = _extract_json(content)
                if parsed is None:
                    raise ForgeError("The model did not return valid JSON.")
                return parsed
            return content
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            if "rate limit" in msg or "429" in msg:
                time.sleep(2.5 * (attempt + 1))
                continue
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise ForgeError(f"Groq API call failed: {e}") from last_err
    raise ForgeError(f"Groq API call failed after retries: {last_err}")


# --------------------------------------------------------------------------
# Stage 1 — Profiles
# --------------------------------------------------------------------------

def extract_profiles(cv_text, jd_text, company_name):
    system = (
        "You are an expert technical recruiter and career coach. You read a "
        "resume/CV and a job description and produce a precise, structured "
        "profile of each. Respond with ONLY a single JSON object, no prose, "
        "no markdown fences."
    )
    user = f"""
Build two profiles from the material below.

=== CANDIDATE CV ===
{cv_text}

=== JOB DESCRIPTION ===
{jd_text}

=== COMPANY (optional, may be empty) ===
{company_name or "Not provided"}

Return JSON with this exact shape:
{{
  "candidate_profile": {{
    "name": "",
    "headline": "one line professional summary",
    "years_experience": "e.g. 4 years",
    "top_skills": ["..."],
    "key_achievements": ["quantified achievement statements"],
    "employment_history": [
      {{"company": "", "title": "", "duration": "", "highlights": ["..."]}}
    ],
    "education": ["..."],
    "certifications": ["..."],
    "potential_gaps_or_flags": ["career gaps, short tenures, unclear items"]
  }},
  "job_profile": {{
    "role_title": "",
    "company": "",
    "seniority": "",
    "must_have_skills": ["..."],
    "nice_to_have_skills": ["..."],
    "core_responsibilities": ["..."],
    "culture_or_values_signals": ["inferred from JD wording / company"],
    "keywords": ["ATS-style keywords found in the JD"]
  }}
}}
"""
    return call_llm(system, user, temperature=0.2)


# --------------------------------------------------------------------------
# Stage 2 — Information check + follow-up loop
# --------------------------------------------------------------------------

def check_information_sufficiency(candidate_profile, job_profile):
    system = (
        "You are a meticulous interview-prep analyst. You decide whether "
        "there is enough information to build a strong, personalized "
        "interview strategy, or whether a few clarifying questions to the "
        "candidate would materially improve the result. Be conservative: "
        "only ask questions that would truly change the strategy. Respond "
        "with ONLY a JSON object."
    )
    user = f"""
CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

JOB PROFILE:
{json.dumps(job_profile, indent=2)}

Return JSON:
{{
  "status": "sufficient" or "missing_info",
  "missing_points": ["short bullet list of what's unclear or missing"],
  "followup_questions": [
    {{"id": "q1", "question": "...", "why_it_matters": "..."}}
  ]
}}
If status is "sufficient", followup_questions should be an empty list.
Limit to at most 5 follow-up questions, only the highest-value ones.
"""
    return call_llm(system, user, temperature=0.2)


def apply_followup_answers(candidate_profile, job_profile, qa_pairs):
    system = (
        "You update a candidate profile with new information the candidate "
        "just supplied, resolving previously missing or unclear points. "
        "Keep everything else intact. Respond with ONLY a JSON object."
    )
    user = f"""
CURRENT CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

JOB PROFILE (for context, do not change it):
{json.dumps(job_profile, indent=2)}

NEW ANSWERS FROM THE CANDIDATE:
{json.dumps(qa_pairs, indent=2)}

Return the FULL updated candidate_profile JSON object using the same shape
as the input candidate profile (name, headline, years_experience,
top_skills, key_achievements, employment_history, education,
certifications, potential_gaps_or_flags), with the new information merged
in and outdated flags removed where resolved.
"""
    return call_llm(system, user, temperature=0.2)


# --------------------------------------------------------------------------
# Stage 3 — Job match analysis
# --------------------------------------------------------------------------

def job_match_analysis(candidate_profile, job_profile):
    system = (
        "You are a sharp hiring manager evaluating role fit. Be honest and "
        "specific, not flattering. Respond with ONLY a JSON object."
    )
    user = f"""
CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

JOB PROFILE:
{json.dumps(job_profile, indent=2)}

Return JSON:
{{
  "match_score": 0-100,
  "strengths": ["concrete overlaps between candidate and role"],
  "gaps": ["real gaps versus the job requirements"],
  "summary": "2-3 sentence honest verdict on fit"
}}
"""
    return call_llm(system, user, temperature=0.3)


# --------------------------------------------------------------------------
# Stage 4 — Interview risk engine (SWOT / pitch / risk areas)
# --------------------------------------------------------------------------

def interview_risk_engine(candidate_profile, job_profile, match_analysis):
    system = (
        "You are an elite interview strategist. Build a SWOT analysis for "
        "this candidate against this specific role, craft elevator pitches, "
        "and flag the interview risk areas most likely to trip them up. "
        "Respond with ONLY a JSON object."
    )
    user = f"""
CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

JOB PROFILE:
{json.dumps(job_profile, indent=2)}

MATCH ANALYSIS:
{json.dumps(match_analysis, indent=2)}

Return JSON:
{{
  "swot": {{
    "strengths": ["..."], "weaknesses": ["..."],
    "opportunities": ["..."], "threats": ["..."]
  }},
  "pitch": {{
    "pitch_30s": "a tight 30-second self-introduction, ~75 words",
    "pitch_60s": "a fuller 60-second self-introduction, ~150 words",
    "pitch_hr_angle": "how to frame the pitch for an HR/recruiter screen",
    "pitch_tech_angle": "how to frame the pitch for a technical interviewer"
  }},
  "risk_areas": [
    {{"area": "...", "why_risky": "...", "mitigation": "..."}}
  ]
}}
"""
    return call_llm(system, user, temperature=0.5)


# --------------------------------------------------------------------------
# Stage 5 — Question engine
# --------------------------------------------------------------------------

QUESTION_CATEGORIES = [
    "HR", "Behavioral", "Technical", "Resume-Based", "Job-Specific",
    "Company-Specific",
]


def generate_questions(candidate_profile, job_profile, risk_engine, n_per_category=4):
    system = (
        "You are a panel of interviewers (HR, hiring manager, and a senior "
        "engineer/practitioner) preparing realistic interview questions for "
        "this specific candidate and role. Base resume-based questions on "
        "specific lines from the candidate profile. Respond with ONLY a "
        "JSON object."
    )
    user = f"""
CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

JOB PROFILE:
{json.dumps(job_profile, indent=2)}

RISK ANALYSIS:
{json.dumps(risk_engine, indent=2)}

Generate up to {n_per_category} realistic interview questions for EACH of
these categories: {", ".join(QUESTION_CATEGORIES)}.

Return JSON:
{{
  "HR": [{{"id": "hr1", "question": "..."}}],
  "Behavioral": [{{"id": "beh1", "question": "..."}}],
  "Technical": [{{"id": "tech1", "question": "..."}}],
  "Resume-Based": [{{"id": "res1", "question": "..."}}],
  "Job-Specific": [{{"id": "job1", "question": "..."}}],
  "Company-Specific": [{{"id": "co1", "question": "..."}}]
}}
IDs must be unique across the whole response.
"""
    return call_llm(system, user, temperature=0.6)


# --------------------------------------------------------------------------
# Stage 6 — Question priority
# --------------------------------------------------------------------------

def prioritize_questions(all_questions_flat):
    system = (
        "You triage interview questions by how likely they are to be asked "
        "and how much they matter to the hiring decision. Respond with "
        "ONLY a JSON object."
    )
    user = f"""
QUESTIONS (id, category, question):
{json.dumps(all_questions_flat, indent=2)}

For every question, assign a priority of "High", "Medium", or "Low".

Return JSON:
{{
  "priorities": [{{"id": "...", "priority": "High"}}]
}}
Every id from the input must appear exactly once in the output.
"""
    return call_llm(system, user, temperature=0.2)


# --------------------------------------------------------------------------
# Stage 7 — Answer blueprint
# --------------------------------------------------------------------------

def build_answer_blueprints(questions_batch, candidate_profile, job_profile):
    system = (
        "You build answer blueprints that help a candidate structure their "
        "own authentic answer — you do not write generic filler. Ground "
        "'cv_evidence' in specifics that actually appear in the candidate "
        "profile. Respond with ONLY a JSON object."
    )
    user = f"""
CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

JOB PROFILE:
{json.dumps(job_profile, indent=2)}

QUESTIONS TO BUILD BLUEPRINTS FOR:
{json.dumps(questions_batch, indent=2)}

Return JSON:
{{
  "blueprints": [
    {{
      "id": "same id as input question",
      "why_asked": "what the interviewer is really probing for",
      "what_to_show": ["2-4 specific qualities/skills to demonstrate"],
      "cv_evidence": ["specific items from the candidate profile to cite"],
      "answer_outline": "a short structured outline (e.g. STAR steps) the
        candidate can fill in with their own words"
    }}
  ]
}}
"""
    return call_llm(system, user, temperature=0.4)


# --------------------------------------------------------------------------
# Stage 8 — Tough question coach
# --------------------------------------------------------------------------

def tough_question_coach(question, candidate_profile, blueprint):
    system = (
        "You are a tough-but-fair interview coach who specializes in the "
        "hardest, most pressure-testing questions. Respond with ONLY a "
        "JSON object."
    )
    user = f"""
QUESTION:
{question}

CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

EXISTING ANSWER BLUEPRINT:
{json.dumps(blueprint, indent=2)}

Return JSON:
{{
  "why_this_is_tough": "...",
  "common_trap": "the mistake most candidates make on this question",
  "coaching_tips": ["3-5 concrete tips"],
  "strong_sample_answer": "a strong first-person model answer, ~120 words,
    written using details from the candidate profile"
}}
"""
    return call_llm(system, user, temperature=0.5)


# --------------------------------------------------------------------------
# Stage 9 — Battle plan + Forge score
# --------------------------------------------------------------------------

def build_battle_plan(candidate_profile, job_profile, match_analysis, risk_engine):
    system = (
        "You compile a concise, actionable interview battle plan. Respond "
        "with ONLY a JSON object."
    )
    user = f"""
CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

JOB PROFILE:
{json.dumps(job_profile, indent=2)}

MATCH ANALYSIS:
{json.dumps(match_analysis, indent=2)}

RISK ENGINE OUTPUT:
{json.dumps(risk_engine, indent=2)}

Return JSON:
{{
  "battle_plan": [
    {{"phase": "Before the interview", "actions": ["..."]}},
    {{"phase": "Opening / first 10 minutes", "actions": ["..."]}},
    {{"phase": "During the interview", "actions": ["..."]}},
    {{"phase": "Closing / questions for them", "actions": ["..."]}}
  ],
  "key_talking_points": ["3-6 points the candidate must land no matter what"]
}}
"""
    return call_llm(system, user, temperature=0.4)


def compute_forge_score(candidate_profile, job_profile, match_analysis,
                         risk_engine, blueprints_summary):
    system = (
        "You score how ready a candidate is for this specific interview. "
        "Be a realistic, slightly demanding grader — scores above 90 should "
        "be rare. Respond with ONLY a JSON object."
    )
    user = f"""
CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)}

JOB PROFILE:
{json.dumps(job_profile, indent=2)}

MATCH ANALYSIS:
{json.dumps(match_analysis, indent=2)}

RISK ENGINE OUTPUT:
{json.dumps(risk_engine, indent=2)}

PREP DONE SO FAR (answer blueprints summary):
{json.dumps(blueprints_summary, indent=2)}

Return JSON:
{{
  "forge_score": 0-100,
  "job_fit": 0-100,
  "technical_readiness": 0-100,
  "behavioral_readiness": 0-100,
  "top_improvement_areas": [
    {{"area": "...", "action": "specific next step to improve it"}}
  ]
}}
"""
    return call_llm(system, user, temperature=0.3)


# --------------------------------------------------------------------------
# Stage 10 — Practice & refine loop
# --------------------------------------------------------------------------

def practice_feedback(question, user_answer, blueprint, candidate_profile):
    system = (
        "You are a warm but rigorous interview coach grading a practice "
        "answer. Be specific and actionable, never generic. Respond with "
        "ONLY a JSON object."
    )
    user = f"""
QUESTION:
{question}

ANSWER BLUEPRINT (what a strong answer should cover):
{json.dumps(blueprint, indent=2)}

CANDIDATE'S PRACTICE ANSWER:
{user_answer}

CANDIDATE PROFILE (for context):
{json.dumps(candidate_profile, indent=2)}

Return JSON:
{{
  "score": 0-100,
  "feedback": "2-3 sentence overall verdict",
  "strengths": ["what worked"],
  "improve": ["specific, actionable fixes"],
  "revised_answer": "a tightened version of the candidate's own answer,
    keeping their voice and facts, ~100-150 words"
}}
"""
    return call_llm(system, user, temperature=0.4)
