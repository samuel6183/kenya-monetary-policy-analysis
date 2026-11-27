"""Canonical dataset analysis; reproducible retrospective evaluation."""
import argparse, hashlib, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller,kpss
from statsmodels.tsa.api import VAR
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox
HASH="444a98058e22f669b103385227511d0f149e39b9644f5b0f40df6fffbd2c714e"
CORE=["CENTRAL_BANK_RATE","LENDING","INFLATION_YOY"]
def run(path,output):
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==HASH
    d=pd.read_csv(path); d.index=pd.PeriodIndex(d.pop("DATE"),freq="M")
    assert d.index.equals(pd.period_range("2016-11","2026-09",freq="M"))
    assert d[CORE].notna().all().all()
    n=d.select_dtypes("number"); t=Path(output)/"tables"; f=Path(output)/"figures"
    t.mkdir(parents=True,exist_ok=True); f.mkdir(parents=True,exist_ok=True)
    def save(name):
        plt.tight_layout(); plt.savefig(f/(name+".svg"),bbox_inches="tight"); plt.close("all")
    def plot(cols,name,title):
        ax=n[cols].to_timestamp().plot(figsize=(10,4),grid=True,title=title); ax.set_ylabel("Percent"); save(name)
    plot(CORE,"policy_transmission","Policy rate, lending and inflation | Kenya")
    plot(["91_DAY_TBILL","182_DAYS_TBILL","364_DAYS_TBILL"],"treasury_yields","Treasury bill yields")
    plot(["INTERBANK_RATE","REPO","REVERSE_REPO","CASH_RESERVE_REQUIREMENT"],"liquidity","Liquidity indicators (missing values not filled)")
    plot(["LENDING","OVERDRAFT","DEPOSIT","SAVINGS"],"bank_rates","Commercial bank rates")
    (n.LENDING-n.CENTRAL_BANK_RATE).to_timestamp().plot(figsize=(10,4),title="Lending minus policy rate (percentage points)",grid=True); save("lending_spread")
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for (base,g),ax in zip(d.groupby("CPI_BASE",sort=False),axes):
        g.KENYA_CPI.to_timestamp().plot(ax=ax,title=base,grid=True); ax.set_ylabel("Published CPI index")
    save("cpi_by_base")
    n.describe().T.to_csv(t/"descriptive.csv"); n.isna().sum().to_csv(t/"missing.csv",header=["missing"]); n.drop(columns="KENYA_CPI").corr().to_csv(t/"level_correlations.csv")
    corr=n[CORE].diff().corr(); fig,ax=plt.subplots(figsize=(6,5)); im=ax.imshow(corr,vmin=-1,vmax=1,cmap="coolwarm"); ax.set_xticks(range(3),CORE,rotation=35,ha="right"); ax.set_yticks(range(3),CORE); fig.colorbar(im); save("change_correlations")
    tests=[]
    for c in CORE:
        for form,s in [("level",n[c]),("difference",n[c].diff().dropna())]:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore"); a=adfuller(s,autolag="AIC"); k=kpss(s,regression="c",nlags="auto")
            tests.append(dict(variable=c,form=form,ADF_stat=a[0],ADF_p=a[1],KPSS_stat=k[0],KPSS_p_bound=k[1]))
    pd.DataFrame(tests).to_csv(t/"stationarity.csv",index=False)
    z=n[CORE].diff().rename(columns={c:"d_"+c for c in CORE}).dropna()
    reg=[]
    for target in ["d_LENDING","d_INFLATION_YOY"]:
        x=z.shift(1).dropna(); y=z.loc[x.index,target]; fit=sm.OLS(y,sm.add_constant(x)).fit(cov_type="HAC",cov_kwds={"maxlags":6})
        for term in fit.params.index:
            reg.append(dict(target=target,term=term,coef=fit.params[term],se=fit.bse[term],p=fit.pvalues[term],lo=fit.conf_int().loc[term,0],hi=fit.conf_int().loc[term,1],n=int(fit.nobs),r2=fit.rsquared))
        (t/(target+"_summary.txt")).write_text(fit.summary().as_text()); acorr_ljungbox(fit.resid,lags=[6,12],return_df=True).to_csv(t/(target+"_ljungbox.csv"))
    pd.DataFrame(reg).to_csv(t/"regression.csv",index=False)
    model=VAR(z.to_timestamp()); selection=model.select_order(6); order=int(selection.selected_orders["bic"]); lag=max(1,order); fit=model.fit(lag)
    pd.DataFrame(selection.ics).rename_axis("lag").to_csv(t/"var_lag_selection.csv")
    fit.params.to_csv(t/"var_coefficients.csv"); fit.pvalues.to_csv(t/"var_pvalues.csv"); (t/"var_summary.txt").write_text(str(fit.summary()))
    white=fit.test_whiteness(nlags=12,adjusted=True); normal=fit.test_normality(); stable=bool(fit.is_stable())
    diag=dict(bic_selected=order,fitted_lag=lag,n=int(fit.nobs),stable=stable,whiteness_p=float(white.pvalue),normality_p=float(normal.pvalue),max_companion_eigenvalue=float(1/min(abs(fit.roots))))
    (t/"var_diagnostics.json").write_text(json.dumps(diag,indent=2))
    if stable:
        fit.irf(12).plot(orth=False,plot_stderr=True,signif=.05); save("var_impulse_responses")
    rows=[]; y=n.INFLATION_YOY
    for i in range(len(y)-24,len(y)):
        train=y.iloc[:i].to_numpy(); ar=sm.OLS(train[1:],sm.add_constant(train[:-1],has_constant="add")).fit()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore"); arima=ARIMA(train,order=(1,1,0)).fit()
        vtrain=z.loc[z.index<y.index[i]]; vfit=VAR(vtrain.to_timestamp()).fit(2); vp=vfit.forecast(vtrain.to_numpy()[-2:],1)[0,2]+train[-1]
        rows.append(dict(DATE=str(y.index[i]),actual=y.iloc[i],persistence=train[-1],seasonal_naive=train[-12],AR1=ar.params[0]+ar.params[1]*train[-1],ARIMA110=float(arima.forecast()[0]),VAR2=vp,arima_converged=bool(arima.mle_retvals.get("converged",False))))
    pred=pd.DataFrame(rows); pred.to_csv(t/"forecast_holdout.csv",index=False); scores=[]
    for c in ["persistence","seasonal_naive","AR1","ARIMA110","VAR2"]:
        e=pred[c]-pred.actual; scores.append(dict(model=c,MAE=float(e.abs().mean()),RMSE=float(np.sqrt((e**2).mean())),bias=float(e.mean())))
    scores=pd.DataFrame(scores).sort_values("RMSE"); scores.to_csv(t/"forecast_metrics.csv",index=False)
    pred.set_index("DATE").drop(columns="arima_converged").plot(figsize=(12,5),title="One-month-ahead inflation | Oct 2024–Sep 2026"); save("forecast_holdout")
    scores.set_index("model")[["MAE","RMSE"]].plot.bar(figsize=(8,4),rot=20,title="Chronological forecast errors (percentage points)"); save("forecast_comparison")
    report={"sha256":HASH,"months":len(d),"var":diag,"forecast":scores.to_dict("records"),"arima_nonconverged":int((~pred.arima_converged).sum())}
    (t/"run.json").write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--input",default="data/processed/kenya_monetary_policy_audited.csv");p.add_argument("--output",default="outputs/audited");a=p.parse_args();run(a.input,a.output)
