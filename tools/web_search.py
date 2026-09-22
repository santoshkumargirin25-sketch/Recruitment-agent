from __future__ import annotations
import requests
class WebSearchClient:
    def __init__(self,provider,key): self.provider=provider.lower(); self.key=key
    def search(self,q):
        if self.provider=="tavily": url,payload,headers="https://api.tavily.com/search",{"api_key":self.key,"query":q,"search_depth":"advanced","max_results":8},{}
        elif self.provider=="serper": url,payload,headers="https://google.serper.dev/search",{"q":q,"num":8},{"X-API-KEY":self.key,"Content-Type":"application/json"}
        else: raise RuntimeError("Unsupported SEARCH_PROVIDER")
        r=requests.post(url,json=payload,headers=headers,timeout=45)
        if not r.ok: raise RuntimeError(f"Web search API error {r.status_code}: {r.text[:400]}")
        data=r.json(); items=data.get("results",[]) if self.provider=="tavily" else data.get("organic",[])
        return [{"title":x.get("title"),"url":x.get("url") or x.get("link"),"snippet":x.get("content") or x.get("snippet"),"query":q,"source":"live_web_search"} for x in items if x.get("url") or x.get("link")]
