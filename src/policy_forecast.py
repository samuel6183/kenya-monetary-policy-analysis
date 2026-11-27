"""Reproduce the recovered two-series study without inventing lending data."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.analysis import forecast

def main():
    df=pd.read_csv("data/processed/policy_inflation_monthly.csv")
    df.index=pd.PeriodIndex(df.pop("DATE"),freq="M")
    expected=pd.period_range("2016-11","2026-09",freq="M")
    if not df.index.equals(expected) or not np.isfinite(df.to_numpy()).all():
        raise ValueError("Invalid recovered monthly panel")
    events=pd.read_csv("data/raw/cbr_changes.csv",parse_dates=["DATE"]).sort_values("DATE")
    month_ends=expected.to_timestamp(how="end").normalize()
    rebuilt=pd.merge_asof(pd.DataFrame({"DATE":month_ends}),events,on="DATE")
    if not np.allclose(rebuilt.CENTRAL_BANK_RATE,df.CENTRAL_BANK_RATE):
        raise ValueError("Policy rate mismatch")
    tables=Path("outputs/tables"); figures=Path("outputs/figures")
    tables.mkdir(parents=True,exist_ok=True); figures.mkdir(parents=True,exist_ok=True)
    pred=forecast(df.INFLATION_YOY)
    pred.to_csv(tables/"recovered_inflation_holdout.csv",index=False)
    scores=[]
    for model in ["AR1","persistence"]:
        err=pred[model]-pred.actual
        scores.append({"model":model,"MAE":err.abs().mean(),"RMSE":np.sqrt((err**2).mean())})
    pd.DataFrame(scores).to_csv(tables/"recovered_forecast_metrics.csv",index=False)
    ax=df.to_timestamp().plot(figsize=(12,5),ylabel="Percent",title="Kenya: month-end CBR and year-on-year inflation")
    ax.figure.tight_layout()
    ax.figure.savefig(figures/"policy_inflation.png",dpi=160)
    plt.close("all")
    pred.set_index("DATE").plot(figsize=(10,4),marker="o",title="Inflation: 12-month one-step holdout")
    plt.tight_layout(); plt.savefig(figures/"recovered_forecast.png",dpi=160); plt.close("all")
    print(scores)
if __name__=="__main__":
    main()
