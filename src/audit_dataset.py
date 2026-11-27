"""Check the immutable audited release; do not impute or change source values."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

PATH=Path("data/processed/kenya_monetary_policy_audited.csv")
MANIFEST=Path("data/processed/cpi_source_manifest.csv")
EXPECTED_HASH="444a98058e22f669b103385227511d0f149e39b9644f5b0f40df6fffbd2c714e"
MISSING={"182_DAYS_TBILL":1,"REPO":32,"REVERSE_REPO":41}
COLS=["CENTRAL_BANK_RATE","INTERBANK_RATE","CASH_RESERVE_REQUIREMENT","91_DAY_TBILL","182_DAYS_TBILL","364_DAYS_TBILL","DEPOSIT","SAVINGS","LENDING","OVERDRAFT","REPO","REVERSE_REPO","INFLATION_YOY","KENYA_CPI"]
def audit(path=PATH,manifest=MANIFEST):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==EXPECTED_HASH,"Snapshot checksum mismatch"
    d=pd.read_csv(path)
    assert list(d.columns)==["DATE",*COLS,"CPI_BASE"]
    expected=pd.period_range("2016-11","2026-09",freq="M").astype(str).tolist()
    assert d.DATE.tolist()==expected
    numeric=d[COLS].apply(pd.to_numeric,errors="raise")
    assert not np.isinf(numeric.to_numpy()).any()
    assert (numeric.KENYA_CPI>0).all()
    missing=numeric.isna().sum().to_dict()
    assert missing=={c:MISSING.get(c,0) for c in COLS}
    assert d.CPI_BASE.tolist()==["February 2009=100"]*39+["February 2019=100"]*80
    same=d.CPI_BASE.eq(d.CPI_BASE.shift(12))
    err=(numeric.KENYA_CPI.pct_change(12)*100-numeric.INFLATION_YOY).abs()[same]
    assert len(err)==95 and err.max()<.05
    covered=[]
    for row in pd.read_csv(manifest).itertuples(index=False):
        covered.extend(pd.period_range(row.START,row.END,freq="M").astype(str))
    assert covered==expected
    report={"sha256":digest,"rows":len(d),"numeric_series":len(COLS),"duplicate_months":int(d.DATE.duplicated().sum()),"missing_cells":int(sum(missing.values())),"missing_by_series":missing,"same_base_yoy_checks":len(err),"max_yoy_abs_diff_pp":float(err.max())}
    print(json.dumps(report,indent=2))
    return report
if __name__=="__main__":
    audit()
