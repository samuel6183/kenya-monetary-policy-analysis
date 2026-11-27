"""Collect official CBK tables and extract candidate KNBS PDF text.

HTML tables may be paginated by the provider. Never infer absent rows.
KNBS text extraction is for manual verification, not automated numeric claims.
"""
from pathlib import Path
from io import StringIO
import argparse
import hashlib
import json
import re
import pandas as pd
import requests
import fitz

RAW = Path("data/raw")
SOURCES = {
    "central_bank_rates": "https://www.centralbank.go.ke/central-bank-rates/",
    "commercial_bank_rates": "https://www.centralbank.go.ke/commercial-banks-weighted-average-rates/",
}
JUNE_2022 = "https://repository.knbs.or.ke/server/api/core/bitstreams/ef9f91c0-5cc5-4c97-aca0-48a5c7f0f7f7/content"

def download(url):
    response = requests.get(url, timeout=60, headers={"User-Agent":"KenyaMonetaryPolicyResearch/1.0"})
    response.raise_for_status()
    return response.content

def collect_cbk():
    """Save all matching table rows, including conflicting observations."""
    RAW.mkdir(parents=True, exist_ok=True)
    manifest=[]
    for name,url in SOURCES.items():
        try:
            content=download(url)
            (RAW/f"{name}.html").write_bytes(content)
            tables=pd.read_html(StringIO(content.decode("utf-8",errors="replace")),displayed_only=False)
            frames=[]
            for table in tables:
                table.columns=[str(c[-1] if isinstance(c,tuple) else c).strip().lower() for c in table.columns]
                if {"year","month"}.issubset(table.columns):
                    frames.append(table)
            if not frames:
                raise ValueError("No expected year/month table")
            df=pd.concat(frames,ignore_index=True).drop_duplicates()
            df["source_url"]=url
            df.to_csv(RAW/f"{name}.csv",index=False)
            manifest.append({"source":name,"url":url,"rows":len(df),"sha256":hashlib.sha256(content).hexdigest()})
        except Exception as exc:
            manifest.append({"source":name,"url":url,"error":str(exc)})
    (RAW/"collection_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))

def extract_knbs(url=JUNE_2022, name="KNBS_LEI_June_2022"):
    """Download PDF, validate signature, save full relevant pages."""
    folder=RAW/"knbs_reports"
    folder.mkdir(parents=True,exist_ok=True)
    if not re.fullmatch(r"[A-Za-z0-9_-]+",name):
        raise ValueError("Invalid filename")
    content=download(url)
    if not content.startswith(b"%PDF"):
        raise ValueError("Response is not a PDF")
    path=folder/f"{name}.pdf"
    path.write_bytes(content)
    hits=[]
    with fitz.open(path) as doc:
        for i,page in enumerate(doc,1):
            text=page.get_text()
            if "consumer price" in text.lower() or "inflation" in text.lower():
                hits.append(f"PAGE {i}\n{text}")
        pages=len(doc)
    (folder/f"{name}.txt").write_text("\n\n".join(hits),encoding="utf-8")
    (folder/f"{name}.json").write_text(json.dumps({"source_url":url,"sha256":hashlib.sha256(content).hexdigest(),"pages":pages,"matched_pages":len(hits)},indent=2))
    print(f"{pages} pages; {len(hits)} candidate pages. Verify actual table cells before entering data.")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("source",choices=["cbk","knbs"])
    parser.add_argument("--url",default=JUNE_2022)
    parser.add_argument("--name",default="KNBS_LEI_June_2022")
    args=parser.parse_args()
    if args.source=="cbk":
        collect_cbk()
    else:
        extract_knbs(args.url,args.name)
