#!/usr/bin/env python3
"""Evidence-based recruitment research agent using live public APIs only."""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from tools.evidence import build_candidate_evidence, deduplicate_candidates
from tools.github_search import GitHubClient
from tools.web_search import WebSearchClient
load_dotenv()

def require_env() -> None:
    required = ["LLM_API_KEY", "GITHUB_TOKEN", "SEARCH_API_KEY", "SEARCH_PROVIDER"]
    missing = [x for x in required if not os.getenv(x)]
    if missing: raise RuntimeError("Missing required environment variables: " + ", ".join(missing) + ". Copy .env.example to .env; no mock data is used.")
    if os.getenv("SEARCH_PROVIDER", "").lower() not in {"tavily", "serper"}: raise RuntimeError("SEARCH_PROVIDER must be tavily or serper")

def llm_json(system: str, user: str) -> dict[str, Any]:
    import requests
    base = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {"model": os.getenv("LLM_MODEL", "gpt-4o-mini"), "temperature": 0, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    r = requests.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}", "Content-Type": "application/json"}, json=payload, timeout=90)
    if not r.ok: raise RuntimeError(f"LLM API error {r.status_code}: {r.text[:500]}")
    content = r.json()["choices"][0]["message"]["content"]
    try: return json.loads(content)
    except json.JSONDecodeError as e: raise RuntimeError(f"LLM returned non-JSON output: {content[:500]}") from e

def extract_job_requirements(job: str) -> dict[str, Any]:
    return llm_json("Extract only requirements explicitly supported by the job description. Return JSON keys role, required_skills, preferred_skills, technologies, experience_requirements, education_requirements, domain_requirements, project_requirements. Use arrays and do not invent requirements.", job)

def generate_search_strategy(reqs: dict[str, Any]) -> dict[str, Any]:
    return llm_json("Create a conservative live-search strategy. Return JSON keys github_user_queries, github_repo_queries, web_queries. Use short GitHub syntax and public professional evidence queries. Do not name fictional people or include results.", json.dumps(reqs))

def analyze_candidates(reqs: dict[str, Any], candidates: list[dict[str, Any]], round_no: int) -> dict[str, Any]:
    return llm_json("You are an evidence auditor. Analyze only supplied evidence. For every requirement use verified, partially_verified, not_verified, or conflicting, with evidence and source URLs. Return candidates, needs_more_search, and follow_up_queries. Say Insufficient public evidence where appropriate. Never infer a skill from a keyword alone. Round " + str(round_no), json.dumps({"requirements": reqs, "candidates": candidates}))

def run(job: str) -> dict[str, Any]:
    require_env(); github = GitHubClient(os.environ["GITHUB_TOKEN"]); web = WebSearchClient(os.environ["SEARCH_PROVIDER"], os.environ["SEARCH_API_KEY"])
    requirements = extract_job_requirements(job); strategy = generate_search_strategy(requirements); raw = []
    for q in strategy.get("github_user_queries", [])[:5]: raw.extend(github.search_users(q))
    for q in strategy.get("github_repo_queries", [])[:5]: raw.extend(github.search_repositories(q))
    for q in strategy.get("web_queries", [])[:5]: raw.extend(web.search(q))
    candidates = deduplicate_candidates(raw)
    for c in candidates: c["evidence"] = build_candidate_evidence(c, github, web)
    decision = analyze_candidates(requirements, candidates, 1); analyses = decision.get("candidates", [])
    rounds = 1
    for rounds in range(2, 4):
        if not decision.get("needs_more_search"): break
        for q in decision.get("follow_up_queries", [])[:4]:
            raw.extend(github.search_users(q)); raw.extend(github.search_repositories(q)); raw.extend(web.search(q))
        candidates = deduplicate_candidates(raw)
        for c in candidates: c["evidence"] = build_candidate_evidence(c, github, web)
        decision = analyze_candidates(requirements, candidates, rounds); analyses = decision.get("candidates", analyses)
    return {"job": job, "requirements": requirements, "search_strategy": strategy, "candidates": analyses, "agent": {"rounds": rounds, "additional_search_requested": bool(decision.get("needs_more_search")), "live_data_only": True}}

def render_markdown(report: dict[str, Any]) -> str:
    out = ["# Recruitment research report", "", "## Job", report["job"], "", "## Extracted requirements", "```json", json.dumps(report["requirements"], indent=2), "```", "", "## Candidates"]
    for c in report.get("candidates", []): out += ["", f"### {c.get('name') or c.get('identifier', 'Unknown public identifier')}", f"- GitHub: {c.get('github_url', 'Not found')}", "```json", json.dumps(c, indent=2), "```"]
    return "\n".join(out + ["", "## Method", "Claims are based on retrieved public evidence and source URLs; missing evidence is not verified."]) + "\n"

def main() -> int:
    p = argparse.ArgumentParser(); g = p.add_mutually_exclusive_group(required=True); g.add_argument("--job"); g.add_argument("--job-file"); p.add_argument("--output-dir", default="reports"); a = p.parse_args()
    try:
        report = run(a.job or Path(a.job_file).read_text(encoding="utf-8")); d = Path(a.output_dir); d.mkdir(exist_ok=True); (d / "recruitment_report.json").write_text(json.dumps(report, indent=2)); (d / "recruitment_report.md").write_text(render_markdown(report)); print(render_markdown(report)); return 0
    except Exception as e: print(f"ERROR: {e}", file=sys.stderr); return 1
if __name__ == "__main__": raise SystemExit(main())
