# 🔥 InterviewForge AI

A free, no-RAG interview-prep copilot. Upload a CV and a job description and
InterviewForge walks you through a full pipeline — profile extraction, job
match analysis, a SWOT-based risk engine, a categorized question bank,
answer blueprints, tough-question coaching, a battle plan, a "Forge Score,"
and a practice loop that feeds weak spots back into your prep.

**Stack (100% free tier):**
- **UI:** [Streamlit](https://streamlit.io)
- **LLM:** [Groq](https://console.groq.com) free API (OpenAI `gpt-oss-120b` / `gpt-oss-20b`)
- **Hosting:** [Streamlit Community Cloud](https://streamlit.io/cloud) (free)

No vector database, no embeddings, no retrieval pipeline — every stage is a
single direct, structured prompt to the LLM using only what's already in
the session (your CV text, the JD, and earlier stage outputs).

---

## 1. Project structure

```
interviewforge/
├── app.py                        # Streamlit UI + pipeline wiring
├── engine.py                     # Groq calls & prompts (the "brain")
├── file_utils.py                 # PDF/DOCX/TXT text extraction
├── styles.py                     # Forge-themed CSS + UI helpers
├── report.py                     # Compiles the final downloadable report
├── requirements.txt
├── .gitignore
└── .streamlit/
    ├── config.toml                # theme
    └── secrets.toml.example       # copy → secrets.toml, add your key
```

## 2. Get a free Groq API key

1. Go to <https://console.groq.com/keys>
2. Sign up (free) and click **Create API Key**
3. Copy the key (starts with `gsk_...`)

Groq's free tier covers everything this app needs — no credit card required.

## 3. Run it locally

```bash
git clone <your-repo-url> interviewforge
cd interviewforge
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then edit .streamlit/secrets.toml and paste your GROQ_API_KEY

streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## 4. Deploy for free on Streamlit Community Cloud

1. Push this folder to a **public or private GitHub repo**.
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. Click **New app**, pick your repo/branch, and set **Main file path** to
   `app.py`.
4. Before (or after) deploying, open **Advanced settings → Secrets** and
   paste:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Click **Deploy**. Your app will be live at
   `https://<your-app-name>.streamlit.app` within a minute or two.

That's the entire stack — Streamlit Cloud, GitHub, and Groq are all free.

## 5. How the pipeline works

| Stage | What happens |
|---|---|
| Setup | Upload/paste a CV and paste a job description |
| Profiles | LLM extracts a structured candidate profile and job profile |
| Information check | LLM flags real gaps and asks up to 5 follow-up questions |
| Job match analysis | Fit score, strengths, gaps |
| Interview risk engine | SWOT, 30s/60s pitches (HR & technical framing), risk areas |
| Question engine | HR, Behavioral, Technical, Resume-based, Job-specific, Company-specific questions |
| Question priority | Each question tagged High / Medium / Low |
| Answer blueprint | Why it's asked, what to show, CV evidence, answer outline |
| Tough question coach | Deep-dive coaching + model answer for the hardest questions |
| Battle plan & Forge Score | Phase-by-phase plan, Job Fit / Technical / Behavioral readiness scores, top improvement areas |
| Practice & refine loop | Write a practice answer, get graded feedback, and push weak spots back into the blueprint/coach stages |

Everything lives in `st.session_state` for the current browser session only
— nothing is written to a database. When you're done, download the full
plan as a Markdown file from the last stage.

## 6. Notable extras built on top of the base pipeline

- **Two model tiers** (`gpt-oss-20b` fast vs. `gpt-oss-120b` higher-quality) selectable in the sidebar — both free on Groq
- **PDF / DOCX / TXT** CV parsing out of the box
- **Resumable stepper navigation** — jump back to any completed stage
- **Automatic retry with backoff** on Groq rate limits
- **One-click Markdown export** of the entire personalized battle plan
- A from-scratch **forge/ironworks visual theme** (not a default template)

## 7. Notes & limits

- Groq's free tier has request-per-minute limits; the app retries
  automatically but very rapid clicking through stages can occasionally
  hit a limit — just wait a few seconds and retry.
- This is a prep tool, not a source of truth — always sanity-check
  generated answers against what's actually true about your background.
