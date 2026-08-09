#!/usr/bin/env python3
from __future__ import annotations

import csv, hashlib, html, json, re, ssl, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE = "https://chatreghermez.com"
OUT = Path("11-projects/red-umbrella/registries")
CSV_OUT = OUT / "chatreghermez-live-url-audit-v1.csv"
JSON_OUT = OUT / "chatreghermez-live-url-audit-v1.json"
MD_OUT = OUT / "chatreghermez-live-url-audit-v1.md"
TIMEOUT = 7
MAX_REDIRECTS = 8
WORKERS = 10
UA = "Mozilla/5.0 (compatible; RedUmbrellaArchitectureAudit/1.1; +https://chatreghermez.com/)"

PATHS = [
"/","/environmental-advertising","/environmental-advertising/","/municipality-investment","/municipality-investment/","/investment/",
"/billboard-rental-isfahan","/billboard-rental-isfahan/","/billboard-mobarakeh","/billboard-mobarakeh/","/cities/mobarakeh/",
"/advertising-foladshahr","/advertising-foladshahr/","/cities/foladshahr/","/billboard-types","/billboard-types/","/structures/",
"/services","/services/","/web-design-isfahan","/web-design-isfahan/","/web-design/","/graphic-design","/graphic-design/",
"/printing","/printing/","/video-marketing-isfahan","/video-marketing-isfahan/","/advertising-video-production/",
"/product-photography","/product-photography/","/social-media-management","/social-media-management/","/consulting","/consulting/",
"/portfolio","/portfolio/","/about","/about/","/about-us","/about-us/","/contact","/contact/","/contact-us","/contact-us/",
"/credentials","/credentials/","/blog","/blog/","/robots.txt","/sitemap.xml","/sitemap_index.xml"]

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title=[]; self.h1=[]; self.canonical=""; self.robots=[]; self.description=""; self.text=[]
        self.in_title=False; self.in_h1=False; self.skip=0
    def handle_starttag(self, tag, attrs):
        tag=tag.lower(); a={str(k).lower():(v or "") for k,v in attrs}
        if tag in {"script","style","noscript","svg"}: self.skip+=1
        if tag=="title": self.in_title=True
        if tag=="h1": self.in_h1=True
        if tag=="link" and "canonical" in a.get("rel","").lower(): self.canonical=a.get("href","").strip()
        if tag=="meta":
            name=a.get("name","").lower(); content=a.get("content","").strip()
            if name in {"robots","googlebot"} and content: self.robots.append(content)
            if name=="description" and content and not self.description: self.description=content
    def handle_endtag(self, tag):
        tag=tag.lower()
        if tag=="title": self.in_title=False
        if tag=="h1": self.in_h1=False
        if tag in {"script","style","noscript","svg"} and self.skip: self.skip-=1
    def handle_data(self,data):
        t=" ".join(data.split())
        if not t: return
        if self.in_title: self.title.append(t)
        if self.in_h1: self.h1.append(t)
        if not self.skip: self.text.append(t)

def clean(s:str,n=500)->str:
    return re.sub(r"\s+"," ",html.unescape(s or "")).strip()[:n]

@dataclass
class Row:
    requested_url:str
    initial_status:str=""; final_status:str=""; final_url:str=""; redirect_hops:int=0; redirect_chain:str=""
    content_type:str=""; title:str=""; h1:str=""; canonical:str=""; meta_robots:str=""; x_robots_tag:str=""; indexable_guess:str=""
    meta_description:str=""; text_sample:str=""; content_bytes:int=0; content_sha256:str=""; error:str=""

def fetch_once(url:str)->Tuple[int,Dict[str,str],bytes]:
    req=Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language":"fa-IR,fa;q=0.9,en;q=0.5","Connection":"close"})
    opener=build_opener(NoRedirect())
    try:
        with opener.open(req,timeout=TIMEOUT) as r: return int(r.getcode()),dict(r.headers.items()),r.read()
    except HTTPError as e:
        try: body=e.read()
        except Exception: body=b""
        return int(e.code),dict(e.headers.items()),body

def audit(url:str)->Row:
    row=Row(url); current=url; chain=[]
    try:
        for hop in range(MAX_REDIRECTS+1):
            status,headers,body=fetch_once(current)
            if hop==0: row.initial_status=str(status)
            loc=headers.get("Location") or headers.get("location")
            if status in {301,302,303,307,308} and loc:
                nxt=urljoin(current,loc); chain.append(f"{status} {current} -> {nxt}"); current=nxt; continue
            row.final_status=str(status); row.final_url=current; row.redirect_hops=len(chain); row.redirect_chain=" || ".join(chain)
            row.content_type=headers.get("Content-Type",headers.get("content-type","")); row.x_robots_tag=headers.get("X-Robots-Tag",headers.get("x-robots-tag",""))
            row.content_bytes=len(body); row.content_sha256=hashlib.sha256(body).hexdigest() if body else ""
            if body and ("text/html" in row.content_type.lower() or b"<html" in body[:500].lower()):
                p=Parser()
                try: p.feed(body.decode("utf-8",errors="replace"))
                except Exception: pass
                row.title=clean(" ".join(p.title),250); row.h1=clean(" | ".join(p.h1),350); row.canonical=clean(p.canonical,500)
                row.meta_robots=clean(", ".join(p.robots),250); row.meta_description=clean(p.description,400); row.text_sample=clean(" ".join(p.text),800)
            flags=(row.meta_robots+" "+row.x_robots_tag).lower()
            row.indexable_guess="YES" if status==200 and "noindex" not in flags else ("NO_NOINDEX" if status==200 else "NO_STATUS")
            return row
        row.error=f"redirect_limit_exceeded:{MAX_REDIRECTS}"; row.final_url=current; row.redirect_hops=len(chain); row.redirect_chain=" || ".join(chain); return row
    except (URLError,TimeoutError,ssl.SSLError,OSError) as e:
        row.error=f"{type(e).__name__}: {e}"; row.final_url=current; row.redirect_hops=len(chain); row.redirect_chain=" || ".join(chain); return row
    except Exception as e:
        row.error=f"{type(e).__name__}: {e}"; row.final_url=current; row.redirect_hops=len(chain); row.redirect_chain=" || ".join(chain); return row

def write(rows:List[Row]):
    OUT.mkdir(parents=True,exist_ok=True); fields=list(asdict(rows[0]).keys())
    with CSV_OUT.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); [w.writerow(asdict(r)) for r in rows]
    JSON_OUT.write_text(json.dumps([asdict(r) for r in rows],ensure_ascii=False,indent=2),encoding="utf-8")
    counts={}
    for r in rows: counts[r.final_status or "ERROR"]=counts.get(r.final_status or "ERROR",0)+1
    lines=["# Red Umbrella — Live URL Audit v1","","**Execution:** GitHub Actions live HTTP audit",f"**Base:** {BASE}",f"**URLs tested:** {len(rows)}","","## Status summary",""]
    for k in sorted(counts): lines.append(f"- `{k}`: {counts[k]}")
    lines += ["","## URLs with errors or non-200 final status",""]
    probs=[r for r in rows if r.error or r.final_status!="200"]
    lines += [f"- `{r.requested_url}` → `{r.final_status or 'ERROR'}` → `{r.final_url}` — {clean(r.error,250)}" for r in probs] or ["- None"]
    lines += ["","## Canonical / redirect observations",""]
    for r in rows:
        if r.redirect_hops or r.canonical: lines.append(f"- `{r.requested_url}` | final `{r.final_status}` `{r.final_url}` | hops `{r.redirect_hops}` | canonical `{r.canonical or '-'}` | title: {r.title or '-'}")
    lines += ["","## Truth note","","This records live HTTP evidence. `indexable_guess` only means final HTTP 200 with no explicit `noindex`; it is not a Google Search Console indexed-state claim.",""]
    MD_OUT.write_text("\n".join(lines),encoding="utf-8")

def main()->int:
    urls=[urljoin(BASE,p) for p in PATHS]; results={}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs={ex.submit(audit,u):u for u in urls}
        for i,fut in enumerate(as_completed(futs),1):
            r=fut.result(); results[r.requested_url]=r
            print(f"[{i}/{len(urls)}] {r.requested_url} initial={r.initial_status or '-'} final={r.final_status or '-'} error={r.error or '-'}",flush=True)
    rows=[results[u] for u in urls]; write(rows)
    ok=sum(1 for r in rows if r.final_status); print(f"Completed with HTTP evidence for {ok}/{len(rows)} URLs")
    return 0 if ok else 2

if __name__=="__main__": sys.exit(main())
