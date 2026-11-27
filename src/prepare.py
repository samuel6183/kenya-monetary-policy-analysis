"""Build a monthly panel without imputing or resolving ambiguous records."""
import argparse
from pathlib import Path
import re
import pandas as pd
import numpy as np

START="2016-11"
END="2026-09"
CORE=["CENTRAL_BANK_RATE","LENDING","INFLATION_YOY"]
ALIASES={"CBR":"CENTRAL_BANK_RATE","LENDING_RATE":"LENDING","CPI":"KENYA_CPI",
         "91_DAY_T_BILL":"91_DAY_TBILL","182_DAY_T_BILL":"182_DAYS_TBILL","364_DAY_T_BILL":"364_DAYS_TBILL"}

def normalize(frame):
    """Standardize headers and map dates to monthly periods."""
    df=frame.copy()
    df.columns=[re.sub(r"[^A-Z0-9]+","_",str(c).upper()).strip("_") for c in df.columns]
    df=df.rename(columns=ALIASES)
    if df.columns.duplicated().any():
        raise ValueError("Duplicate normalized column names")
    if "DATE" not in df:
        if not {"YEAR","MONTH"}.issubset(df.columns):
            raise ValueError("Need DATE or YEAR and MONTH")
        year=pd.to_numeric(df.YEAR,errors="coerce").astype("Int64").astype(str)
        date=pd.to_datetime(year+" "+df.MONTH.astype(str),format="%Y %B",errors="coerce")
        alt=pd.to_datetime(year+" "+df.MONTH.astype(str),format="%Y %b",errors="coerce")
        numeric=pd.to_datetime(year+"-"+df.MONTH.astype(str)+"-01",format="%Y-%m-%d",errors="coerce")
        df["DATE"]=date.fillna(alt).fillna(numeric)
    df["DATE"]=pd.to_datetime(df.DATE,errors="coerce").dt.to_period("M")
    if df.DATE.isna().any():
        raise ValueError("Unparseable dates; inspect source before analysis")
    df=df.drop(columns=["YEAR","MONTH"],errors="ignore")
    return df

def prepare(frames,start=START,end=END):
    calendar=pd.period_range(start,end,freq="M")
    observations=[]
    for frame in frames:
        df=normalize(frame)
        for col in df.columns:
            if col in ["DATE","SOURCE_URL","SOURCE","PAGE","NOTES","CPI_BASE","VERIFIED"]:
                continue
            values=pd.to_numeric(df[col].astype(str).str.replace(",","",regex=False),errors="coerce")
            if np.isinf(values).any():
                raise ValueError("Infinite numeric value")
            observations.append(pd.DataFrame({"DATE":df.DATE,"variable":col,"value":values}))
    if not observations:
        raise ValueError("No observations")
    long=pd.concat(observations,ignore_index=True).dropna(subset=["value"])
    long=long[long.DATE.isin(calendar)].drop_duplicates()
    count=long.groupby(["DATE","variable"]).value.nunique()
    conflicts=count[count>1].reset_index(name="distinct_values")
    if not conflicts.empty:
        long=long.merge(conflicts[["DATE","variable"]].assign(conflict=True),how="left")
        conflict_values=long[long.conflict.eq(True)].drop(columns="conflict")
        long=long[~long.conflict.eq(True)].drop(columns="conflict")
    else:
        conflict_values=long.iloc[:0].copy()
    panel=long.pivot_table(index="DATE",columns="variable",values="value",aggfunc="first").reindex(calendar)
    for col in CORE:
        if col not in panel:
            panel[col]=np.nan
    panel.index.name="DATE"
    return panel,conflict_values

def main():
    p=argparse.ArgumentParser()
    p.add_argument("inputs",nargs="+",help="Source CSVs or earlier combined CSV")
    p.add_argument("--start",default=START)
    p.add_argument("--end",default=END)
    args=p.parse_args()
    panel,conflicts=prepare([pd.read_csv(f) for f in args.inputs],args.start,args.end)
    out=Path("data/processed")
    out.mkdir(parents=True,exist_ok=True)
    panel.to_csv(out/"monthly_panel.csv")
    conflicts.to_csv(out/"conflicts.csv",index=False)
    panel.isna().sum().rename("missing_months").to_csv(out/"coverage.csv")
    panel[CORE].isna().stack().loc[lambda s:s].rename("missing").to_csv(out/"missing_core.csv")
    print(f"Calendar months: {len(panel)}; complete core months: {panel[CORE].dropna().shape[0]}; conflict values: {len(conflicts)}")
    print(panel.isna().sum().to_string())

if __name__=="__main__":
    main()
