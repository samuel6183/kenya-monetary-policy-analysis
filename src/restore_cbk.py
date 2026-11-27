"""Restore the original notebook's successful CBK acquisition (cells 5, 22, 28–42).
Re-download official sources; preserve raw data and record conflicts.
"""
from pathlib import Path
from io import BytesIO
import json
import hashlib
import pandas as pd
import requests
from src.prepare import prepare

RAW=Path("data/raw")
OUT=Path("data/processed")
START,END="2016-11","2026-09"
CENTRAL="https://www.centralbank.go.ke/uploads/interest_rates/648402325_Central%20Bank%20Rates_with%20Heads.csv"
COMMERCIAL="https://www.centralbank.go.ke/commercial-banks-weighted-average-rates/"
AJAX="https://www.centralbank.go.ke/wp-admin/admin-ajax.php?action=get_wdtable&table_id=17"
SEPT="https://www.centralbank.go.ke/uploads/monthly_economic_indicators/476370057_Monthly%20Economic%20Indicators%20September%202023.pdf"
COLS=["YEAR","MONTH","DEPOSIT","SAVINGS","LENDING","OVERDRAFT"]

def fetch_commercial(session):
    rows=[]; total=None
    headers={"User-Agent":"Mozilla/5.0","X-Requested-With":"XMLHttpRequest","Referer":COMMERCIAL}
    while total is None or len(rows)<total:
        r=session.post(AJAX,data={"draw":1,"start":len(rows),"length":100,"search[value]":"","search[regex]":"false"},headers=headers,timeout=60)
        r.raise_for_status()
        j=r.json()
        current=int(j["recordsTotal"])
        if total is not None and current!=total:
            raise ValueError("Source changed during pagination")
        total=current
        batch=j["data"]
        if not batch or len(rows)+len(batch)>total:
            raise ValueError("Incomplete or inconsistent pagination")
        rows.extend(batch)
    return pd.DataFrame(rows,columns=COLS)

def clean_central(content):
    df=pd.read_csv(BytesIO(content),skiprows=1)
    df.columns=[str(c).strip().upper().replace(" ","_").replace("-","_") for c in df.columns]
    df["YEAR"]=pd.to_numeric(df.YEAR,errors="coerce").ffill()
    df["MONTH"]=df.MONTH.astype(str).str.strip().str[:3].str.title()
    df=df[df.MONTH.isin("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()) & df.YEAR.notna()].copy()
    return df

def recover_commercial(raw):
    df=raw.drop_duplicates().copy()
    # Original notebook cites February 2026 Monthly Economic Indicators.
    # Preserve both raw rows and do not resolve deposit/savings without source audit.
    # September 2023 was recovered in notebook cells 30–33 from an official report.
    dates=pd.to_datetime(df.YEAR.astype(str)+" "+df.MONTH.astype(str),format="%Y %B",errors="raise").dt.to_period("M")
    if not dates.eq(pd.Period("2023-09","M")).any():
        df=pd.concat([df,pd.DataFrame([[2023,"September",8.64,4.00,13.98,13.62]],columns=COLS)],ignore_index=True)
    return df

def main():
    RAW.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    with requests.Session() as session:
        r=session.get(CENTRAL,timeout=60); r.raise_for_status()
        (RAW/"central_bank_rates_original.csv").write_bytes(r.content)
        central=clean_central(r.content)
        raw=fetch_commercial(session)
        raw.to_csv(RAW/"commercial_bank_rates_live_cbk.csv",index=False)
        r2=session.get(SEPT,timeout=60); r2.raise_for_status()
        if not r2.content.startswith(b"%PDF"):
            raise ValueError("September report is not PDF")
        (RAW/"cbk_september_2023.pdf").write_bytes(r2.content)
    commercial=recover_commercial(raw)
    panel,conflicts=prepare([central,commercial],START,END)
    panel=panel.drop(columns=["INFLATION_YOY"],errors="ignore")
    panel.to_csv(OUT/"cbk_restored_monthly.csv")
    conflicts.to_csv(OUT/"cbk_restored_conflicts.csv",index=False)
    panel.isna().sum().rename("missing").to_csv(OUT/"cbk_restored_coverage.csv")
    manifest={"central_source":CENTRAL,"central_sha256":hashlib.sha256(r.content).hexdigest(),"commercial_source":AJAX,"commercial_raw_rows":len(raw),"september_source":SEPT,"september_sha256":hashlib.sha256(r2.content).hexdigest(),"september_values":"Recovered from original notebook; pending independent PDF cell check","months":len(panel),"missing":panel.isna().sum().to_dict()}
    (OUT/"cbk_restore_manifest.json").write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
if __name__=="__main__":
    main()
