# Recruitment Agent

Evidence-first CLI research agent for real public candidates. It uses live GitHub REST data, Tavily or Serper web search, and an OpenAI-compatible LLM to extract requirements, create search queries, collect provenance, audit candidates, and request bounded follow-up searches.

## Guarantees

There is no demo mode, seed data, hard-coded person, fake API response, or fallback candidate. Missing credentials fail clearly. Web results are not guessed to belong to people. GitHub candidates are deduplicated only by stable username.

## Setup

Copy `.env.example` to `.env`, fill `LLM_API_KEY`, `GITHUB_TOKEN`, `SEARCH_API_KEY`, and `SEARCH_PROVIDER` (`tavily` or `serper`), then run:

```bash
python -m pip install -r requirements.txt
python agent.py --job "We need a Python engineer with FastAPI and production ML experience."
# or: python agent.py --job-file job.txt
```

Reports are saved to `reports/recruitment_report.json` and `reports/recruitment_report.md`.

## Docker

```bash
docker compose build
docker compose run --rm recruitment-agent --job "We need a Python engineer with FastAPI and production ML experience."
```

## Workflow and tools

`extract_job_requirements` -> `generate_search_strategy` -> `search_github_users`/`search_github_repositories` + `search_web` -> `collect_candidate_evidence` -> `analyze_candidate` -> optional live follow-up search -> report. Analysis preserves requirement-level statuses (`verified`, `partially_verified`, `not_verified`, `conflicting`) and source URLs. Unsupported facts are reported as not verified or insufficient public evidence.

## APIs, privacy, and limitations

GitHub's official API supplies public profiles, repositories, languages, topics, descriptions, and public events. Tavily or Serper supplies public search links. The app does not scrape LinkedIn, bypass login/CAPTCHA/access controls, or access private data. Public data can be incomplete or stale; this is a recruiter research aid, not an employment decision maker. Respect provider terms, rate limits, privacy law, and avoid sensitive/protected characteristics.
