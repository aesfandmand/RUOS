#!/usr/bin/env python3
from __future__ import annotations
import csv, json, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_url_audit as core

core.TIMEOUT = 30
OUT = Path("11-projects/red-umbrella/registries")
CSV_OUT = OUT / "chatreghermez-current-route-probe-v1.csv"
JSON_OUT = OUT / "chatreghermez-current-route-probe-v1.json"
MD_OUT = OUT / "chatreghermez-current-route-probe-v1.md"

# Group A: v2/English target candidates or aliases that must not be assumed live.
# Group B: routes discovered from current internal links, including Persian and English service slugs.
PATHS = [
    "/graphic-design/", "/printing/", "/product-photography/", "/social-media-management/", "/consulting/", "/credentials/", "/blog/",
    "/seo/", "/digital-marketing/", "/website-services/", "/social-media/", "/photography-video/",
    "/advertising-consulting/", "/marketing-consulting/", "/business-consulting/",

    "/graphic-design-services/", "/printed-advertisement/", "/poster-design/", "/instagram-page-management-in-isfahan/",
    "/advertising-photography-in-isfahan/", "/advertising-teaser-design-in-isfahan/", "/advertising-video-and-teaser/", "/video-marketing-in-isfahan/",
    "/website-design-in-isfahan/", "/website-support-in-isfahan/", "/logo-design-in-isfahan/", "/office-set-design-in-isfahan/",
    "/catalog-design-and-printing-in-isfahan/", "/brochure-design-in-isfahan/", "/business-card-design-in-isfahan/",
    "/advertising-campaign-design/", "/advertising-campaign/", "/advertising-media/", "/billboard/", "/advertising/", "/portfolios/",
    "/social-networks/", "/instagram-admin-tasks/",

    "/تبلیغات-محیطی/", "/طراحی-سایت-در-اصفهان/", "/خدمات-سئو-در-اصفهان/", "/طراحی-لوگو-در-اصفهان/",
    "/طراحی-ست-اداری-در-اصفهان/", "/طراحی-و-چاپ-کاتالوگ-در-اصفهان/", "/طراحی-و-چاپ-بروشور-در-اصفهان/",
    "/طراحی-و-چاپ-کارت-ویزیت-در-اصفهان/", "/عکاسی-صنعتی-و-تبلیغاتی-در-اصفهان/", "/طراحی-کمپین-تبلیغاتی/", "/بازاریابی/",
]

def safe_url(path: str) -> str:
    return core.BASE + quote(path, safe="/%:?=&")

def main():
    urls=[safe_url(p) for p in PATHS]; results={}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs={ex.submit(core.audit,u):u for u in urls}
        for i,f in enumerate(as_completed(futs),1):
            r=f.result(); results[r.requested_url]=r
            print(f"[{i}/{len(urls)}] {r.requested_url} => {r.final_status or 'ERROR'} {r.final_url} {r.error}", flush=True)
    rows=[results[u] for u in urls]
    OUT.mkdir(parents=True,exist_ok=True)
    fields=list(asdict(rows[0]).keys())
    with CSV_OUT.open("w",encoding="utf-8-sig",newline="") as fp:
        w=csv.DictWriter(fp,fieldnames=fields); w.writeheader(); [w.writerow(asdict(r)) for r in rows]
    JSON_OUT.write_text(json.dumps([asdict(r) for r in rows],ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Red Umbrella — Current Route Probe v1","",f"URLs tested: {len(rows)}","","## Results",""]
    for path,r in zip(PATHS,rows):
        lines.append(f"- `{path}` → `{r.final_status or 'ERROR'}` `{r.final_url}` | canonical `{r.canonical or '-'}` | title `{r.title or '-'}` | H1 `{r.h1 or '-'}` | error `{r.error or '-'}`")
    lines += ["","## Truth rule","","HTTP evidence only. WordPress may canonical-redirect a non-existing guess to a semantically similar post; a 200 final response after such a redirect does not prove the requested route is a valid canonical target. Migration decisions for live/high-value URLs still require current-route matching plus GSC query/performance and backlink evidence.",""]
    MD_OUT.write_text("\n".join(lines),encoding="utf-8")
    return 0 if any(r.final_status for r in rows) else 2

if __name__ == "__main__": raise SystemExit(main())
