"""Monthly monetary transmission analysis with strict coverage gates."""
import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import acorr_ljungbox
from src.prepare import CORE

def load_panel(path,start="2016-11",end="2026-09"):
    df=pd.read_csv(path)
    df["DATE"]=pd.PeriodIndex(df.DATE,freq="M")
    df=df.set_index("DATE").sort_index()
    expected=pd.period_range(start,end,freq="M")
    if df.index.has_duplicates or not df.index.equals(expected):
        raise ValueError("Panel must contain every calendar month exactly once")
    df=df[CORE].apply(pd.to_numeric,errors="raise")
    if not np.isfinite(df.to_numpy()).all():
        raise ValueError("Core series incomplete; review coverage and resolve missing observations")
    if len(df)<60:
        raise ValueError("At least 60 months required")
    return df

def forecast(inflation,holdout=12):
    """Expanding-window one-step forecasts; fixed AR(1) vs last observation."""
    if holdout<1 or len(inflation)-holdout<36:
        raise ValueError("Insufficient training observations")
    rows=[]
    for i in range(len(inflation)-holdout,len(inflation)):
        y=inflation.iloc[:i].to_numpy()
        X=sm.add_constant(y[:-1],has_constant="add")
        fit=sm.OLS(y[1:],X).fit()
        rows.append({"DATE":str(inflation.index[i]),"actual":inflation.iloc[i],
            "AR1":float(fit.params[0]+fit.params[1]*y[-1]),"persistence":y[-1]})
    return pd.DataFrame(rows)

def analyze(df,out):
    out=Path(out)
    tables=out/"tables"; figures=out/"figures"
    tables.mkdir(parents=True,exist_ok=True); figures.mkdir(parents=True,exist_ok=True)
    df.describe().T.to_csv(tables/"descriptive.csv")
    df.corr().to_csv(tables/"level_correlations_descriptive.csv")
    df.to_timestamp().plot(subplots=True,figsize=(10,8),grid=True,title="Kenya monthly monetary indicators")
    plt.tight_layout(); plt.savefig(figures/"monthly_indicators.png",dpi=150); plt.close("all")
    changes=df[["CENTRAL_BANK_RATE","LENDING"]].diff()
    model_df=pd.DataFrame({"delta_lending":changes.LENDING,
        "lag_delta_cbr":changes.CENTRAL_BANK_RATE.shift(1),
        "lag_delta_lending":changes.LENDING.shift(1),
        "lag_inflation":df.INFLATION_YOY.shift(1)}).dropna()
    fit=sm.OLS(model_df.delta_lending,sm.add_constant(model_df.drop(columns="delta_lending"))).fit(cov_type="HAC",cov_kwds={"maxlags":6})
    pd.DataFrame({"coefficient":fit.params,"std_error":fit.bse,"p_value":fit.pvalues,
        "ci_low":fit.conf_int()[0],"ci_high":fit.conf_int()[1]}).to_csv(tables/"transmission_associations.csv")
    (tables/"regression_summary.txt").write_text(fit.summary().as_text(),encoding="utf-8")
    acorr_ljungbox(fit.resid,lags=[6,12],return_df=True).to_csv(tables/"residual_ljung_box.csv")
    diagnostics=[]
    for col in CORE:
        for form,s in [("level",df[col]),("difference",df[col].diff().dropna())]:
            try:
                stat,p,*_=adfuller(s,autolag="AIC")
                diagnostics.append({"variable":col,"form":form,"adf_stat":stat,"p_value":p})
            except ValueError as exc:
                diagnostics.append({"variable":col,"form":form,"error":str(exc)})
    pd.DataFrame(diagnostics).to_csv(tables/"stationarity.csv",index=False)
    pred=forecast(df.INFLATION_YOY)
    pred.to_csv(tables/"inflation_holdout.csv",index=False)
    scores=[]
    for model in ["AR1","persistence"]:
        err=pred[model]-pred.actual
        scores.append({"model":model,"MAE":err.abs().mean(),"RMSE":np.sqrt((err**2).mean())})
    pd.DataFrame(scores).to_csv(tables/"forecast_metrics.csv",index=False)
    pred.set_index("DATE").plot(figsize=(10,4),marker="o",title="One-step inflation forecasts: chronological holdout")
    plt.tight_layout(); plt.savefig(figures/"forecast_holdout.png",dpi=150); plt.close("all")
    (tables/"run_metadata.json").write_text(json.dumps({"months":len(df),"start":str(df.index[0]),"end":str(df.index[-1]),"regression_n":int(fit.nobs),"forecast_holdout":12,"interpretation":"Associational, not causal. Revised data, not real-time vintages."},indent=2))
    return scores

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="data/processed/monthly_panel.csv")
    parser.add_argument("--output",default="outputs")
    parser.add_argument("--start",default="2016-11")
    parser.add_argument("--end",default="2026-09")
    args=parser.parse_args()
    print(analyze(load_panel(args.input,args.start,args.end),args.output))
