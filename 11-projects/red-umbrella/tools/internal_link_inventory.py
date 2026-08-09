#!/usr/bin/env python3
from __future__ import annotations
import csv, html, sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_url_audit as core

core.TIMEOUT = 35
OUT=Path("11-projects/red-umbrella/registries")
CSV_OUT=OUT/"chatreghermez-current-internal-link-inventory-v1.csv"
MD_OUT=OUT/"chatreghermez-current-internal-link-inventory-v1.md"
SEEDS=["/","/services/","/portfolio/","/about-us/","/contact-us/"]

class LinkParser(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()!="a": return
        a={k.lower():(v or "") for k,v in attrs}
        href=a.get("href","").strip()
        if href: self.links.append(href)

def main():
    rows=[]; unique=set()
    for seed in SEEDS:
        url=urljoin(core.BASE,seed)
        try:
            status,headers,body=core.fetch_once(url)
        except Exception as e:
            rows.append([url,"","","ERROR",str(e)]); continue
        p=LinkParser()
        try: p.feed(body.decode("utf-8",errors="replace"))
        except Exception: pass
        for href in p.links:
            absolute=urljoin(url,href); absolute,_=urldefrag(absolute); parsed=urlparse(absolute)
            if parsed.scheme not in {"http","https"}: continue
            if parsed.netloc.lower() not in {"chatreghermez.com","www.chatreghermez.com"}: continue
            path=parsed.path or "/"
            if parsed.query: path += "?"+parsed.query
            key=(url,path)
            if key in unique: continue
            unique.add(key); rows.append([url,href,path,str(status),""])
    OUT.mkdir(parents=True,exist_ok=True)
    with CSV_OUT.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f); w.writerow(["source_url","raw_href","normalized_internal_path","source_http_status","error"]); w.writerows(rows)
    targets=sorted({r[2] for r in rows if r[2]})
    lines=["# Red Umbrella — Current Internal Link Inventory v1","",f"Seed pages: {len(SEEDS)}",f"Unique source→target edges: {len(rows)}",f"Unique internal targets: {len(targets)}","","## Internal targets",""]
    lines += [f"- `{t}`" for t in targets]
    MD_OUT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"Captured {len(rows)} edges / {len(targets)} targets")
    return 0
if __name__=="__main__": raise SystemExit(main())
