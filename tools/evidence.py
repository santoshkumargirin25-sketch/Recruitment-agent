from __future__ import annotations

def deduplicate_candidates(items):
    merged={}
    for item in items:
        if item.get("github_username"):
            key="github:"+item["github_username"].lower()
            if key not in merged: merged[key]=item
            else:
                old=merged[key]; old["sources"]=sorted(set(old.get("sources",[])+item.get("sources",[]))); known={r["url"] for r in old.get("repositories",[])}; old["repositories"].extend(r for r in item.get("repositories",[]) if r["url"] not in known)
        else:
            key="web:"+str(item.get("url")); merged.setdefault(key,{"identifier":item.get("url"),"name":item.get("title"),"profile_urls":[item.get("url")],"web_evidence":[item],"sources":[item.get("url")]})
    return list(merged.values())

def build_candidate_evidence(candidate,github,web):
    evidence={"profile":{"bio":candidate.get("bio"),"location":candidate.get("location"),"public_repos":candidate.get("public_repos"),"source":candidate.get("github_url")},"repositories":candidate.get("repositories",[]),"public_activity":[],"web_results":candidate.get("web_evidence",[])}
    if candidate.get("github_username"):
        evidence["public_activity"]=[{"type":e.get("type"),"repo":e.get("repo",{}).get("name"),"created_at":e.get("created_at"),"url":candidate.get("github_url")} for e in github.public_events(candidate["github_username"])]
    return evidence
