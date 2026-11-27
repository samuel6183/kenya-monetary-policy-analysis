"""Recover the report catalogue and extract conservative LEI table candidates.
Only paired national CPI/inflation rows with explicit year and six numeric
columns are accepted. All candidates retain report, page and CPI-base evidence.
Human review remains required, especially for layouts and rebasing.
"""
from pathlib import Path
import re
import calendar
import pandas as pd
import requests
import fitz
import hashlib

API="https://repository.knbs.or.ke/server/api"
START,END="2016-11","2026-09"
MONTHS={m.lower():i for i,m in enumerate(calendar.month_name) if m}
MONTH_PATTERN="|".join(calendar.month_name[1:])
REPORT_PATTERN=re.compile(r"(?:consumer price.*inflation|leading economic indicators)",re.I)
DATE_PATTERN=re.compile(r"\b("+MONTH_PATTERN+r")[\s,–-]+(20\d{2})\b",re.I)

def get_json(session,url,**kwargs):
    r=session.get(url,timeout=60,**kwargs);r.raise_for_status();return r.json()

def catalogue(session):
    records={}
    for query in ["Kenya Consumer Price Indices and Inflation Rates","Leading Economic Indicators"]:
        page=0
        while True:
            root=get_json(session,API+"/discover/search/objects",params={"query":query,"size":100,"page":page})
            result=root["_embedded"]["searchResult"]
            for obj in result["_embedded"]["objects"]:
                item=obj["_embedded"]["indexableObject"]
                title=item.get("name","")
                match=DATE_PATTERN.search(title)
                if match and REPORT_PATTERN.search(title):
                    date=f"{match[2]}-{MONTHS[match[1].lower()]:02d}"
                    if START<=date<=END:
                        records[item["uuid"]]={"DATE":date,"TITLE":title,"UUID":item["uuid"]}
            page+=1
            if page>=result["page"]["totalPages"]:break
    return pd.DataFrame(records.values(),columns=["DATE","TITLE","UUID"])

def pdf_for_item(session,uuid):
    root=get_json(session,API+f"/core/items/{uuid}/bundles")
    for b in root["_embedded"]["bundles"]:
        if b["name"]!="ORIGINAL":continue
        bits=get_json(session,API+f"/core/bundles/{b['uuid']}/bitstreams")
        for bit in bits["_embedded"]["bitstreams"]:
            if bit.get("name","").lower().endswith(".pdf"):
                url=API+f"/core/bitstreams/{bit['uuid']}/content"
                r=session.get(url,timeout=60);r.raise_for_status()
                if not r.content.startswith(b"%PDF"):raise ValueError("Not PDF")
                return r.content,url
    raise ValueError("No original PDF")

def parse_table(text):
    """Exact line layout observed in June 2022 LEI notebook cell 64."""
    year=None;result={}
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    for i,line in enumerate(lines):
        if re.fullmatch(r"20\d{2}",line):
            year=int(line);continue
        m=re.fullmatch(r"("+MONTH_PATTERN+r")[.\s]*",line,re.I)
        if not m or year is None:continue
        numbers=lines[i+1:i+7]
        if len(numbers)==6 and all(re.fullmatch(r"[-+]?\d+\.\d+",v) for v in numbers):
            date=f"{year}-{MONTHS[m[1].lower()]:02d}"
            value=float(numbers[-1])
            if date in result and result[date]!=value:raise ValueError("Conflicting table rows")
            result[date]=value
    return result

def extract(content,url,uuid):
    cpi={};infl={};bases={}
    with fitz.open(stream=content,filetype="pdf") as doc:
        for i,page in enumerate(doc,1):
            text=page.get_text()
            if re.search(r"Table\s*1\s*\(a\)\s*:\s*(?:Kenya\s+)?Consumer Price Indices",text,re.I) and "Kenya CPI" in text:
                vals=parse_table(text)
                base=re.search(r"Base period\s*([^\n]+)",text,re.I)
                for date,value in vals.items():
                    cpi[date]=(value,i);bases[date]=base[1].strip() if base else "UNKNOWN"
            if re.search(r"Table\s*1\s*\(b\)\s*:\s*(?:Kenya\s+)?Inflation rate",text,re.I) and "Kenya CPI" in text:
                for date,value in parse_table(text).items():infl[date]=(value,i)
    return [{"DATE":date,"KENYA_CPI":cpi[date][0],"INFLATION_YOY":infl[date][0],"CPI_BASE":bases[date],"SOURCE_URL":url,"SOURCE_UUID":uuid,"CPI_TABLE_PAGE":cpi[date][1],"INFLATION_TABLE_PAGE":infl[date][1],"SHA256":hashlib.sha256(content).hexdigest(),"STATUS":"candidate_requires_review"} for date in sorted(cpi.keys() & infl.keys()) if START<=date<=END]

def main():
    out=Path("data/processed");out.mkdir(parents=True,exist_ok=True)
    raw=Path("data/raw/knbs_reports");raw.mkdir(parents=True,exist_ok=True)
    rows=[];errors=[]
    with requests.Session() as s:
        reports=catalogue(s)
        reports.to_csv(out/"knbs_report_catalogue.csv",index=False)
        lei=reports[reports.TITLE.str.contains("Leading Economic Indicators",case=False,na=False)].sort_values("DATE",ascending=False)
        covered=set()
        for report in lei.itertuples(index=False):
            if report.DATE in covered:continue
            try:
                content,url=pdf_for_item(s,report.UUID)
                (raw/f"{report.UUID}.pdf").write_bytes(content)
                found=extract(content,url,report.UUID)
                rows.extend(found)
                covered.update(r["DATE"] for r in found)
            except Exception as exc:errors.append({"UUID":report.UUID,"error":str(exc)})
    cols=["DATE","KENYA_CPI","INFLATION_YOY","CPI_BASE","SOURCE_URL","SOURCE_UUID","CPI_TABLE_PAGE","INFLATION_TABLE_PAGE","SHA256","STATUS"]
    pd.DataFrame(rows,columns=cols).to_csv(out/"knbs_extraction_candidates.csv",index=False)
    pd.DataFrame(errors,columns=["UUID","error"]).to_csv(out/"knbs_extraction_errors.csv",index=False)
    expected=set(pd.period_range(START,END,freq="M").astype(str))
    print("Catalogue reports:",len(reports),"Candidate months:",len(covered),"Missing:",sorted(expected-covered),"Errors:",len(errors))
if __name__=="__main__":
    main()
