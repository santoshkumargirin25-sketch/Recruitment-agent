from __future__ import annotations
from typing import Any
import requests
class GitHubClient:
    def __init__(self, token: str):
        self.s = requests.Session(); self.s.headers.update({"Accept":"application/vnd.github+json","Authorization":f"Bearer {token}","X-GitHub-Api-Version":"2022-11-28"}); self.base="https://api.github.com"
    def _get(self, path: str, params: dict[str,Any]|None=None):
        r=self.s.get(self.base+path,params=params,timeout=30)
        if not r.ok: raise RuntimeError(f"GitHub API error {r.status_code}: {r.text[:400]}")
        return r.json()
    def search_users(self,q):
        out=[]
        for x in self._get("/search/users",{"q":q,"per_page":10}).get("items",[]): out.append(self._candidate(self._get(f"/users/{x['login']}"),self._get(f"/users/{x['login']}/repos",{"sort":"updated","per_page":30}),f"GitHub user search: {q}"))
        return out
    def search_repositories(self,q):
        out=[]
        for x in self._get("/search/repositories",{"q":q,"per_page":10}).get("items",[]):
            u=x["owner"]["login"]; out.append(self._candidate(self._get(f"/users/{u}"),self._get(f"/users/{u}/repos",{"sort":"updated","per_page":30}),f"GitHub repository search: {q}"))
        return out
    @staticmethod
    def _candidate(p,repos,reason):
        return {"identifier":p["login"],"name":p.get("name") or p["login"],"github_username":p["login"],"github_url":p["html_url"],"bio":p.get("bio"),"location":p.get("location"),"public_repos":p.get("public_repos"),"repositories":[{"name":r["name"],"url":r["html_url"],"description":r.get("description"),"language":r.get("language"),"topics":r.get("topics",[]),"stars":r.get("stargazers_count",0)} for r in repos],"sources":[p["html_url"]],"discovery_reason":reason}
    def public_events(self,u): return self._get(f"/users/{u}/events/public",{"per_page":30})
