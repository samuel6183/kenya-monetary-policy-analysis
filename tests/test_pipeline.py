import unittest
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from src.prepare import prepare
from src.analysis import load_panel,forecast,analyze

class PipelineTests(unittest.TestCase):
    def test_calendar(self):
        p,c=prepare([pd.DataFrame({"DATE":["2020-01","2020-03"],"CBR":[8,7]})],"2020-01","2020-03")
        self.assertEqual(len(p),3)
        self.assertTrue(pd.isna(p.iloc[1].CENTRAL_BANK_RATE))
    def test_conflict(self):
        p,c=prepare([pd.DataFrame({"DATE":["2020-01","2020-01"],"LENDING":[12,12],"DEPOSIT":[4,5]})],"2020-01","2020-01")
        self.assertEqual(p.iloc[0].LENDING,12)
        self.assertTrue("DEPOSIT" not in p or pd.isna(p.iloc[0].DEPOSIT))
        self.assertEqual(len(c),2)
    def test_year_month(self):
        p,c=prepare([pd.DataFrame({"YEAR":[2020],"MONTH":["February"],"CBR":[8]})],"2020-02","2020-02")
        self.assertEqual(p.iloc[0].CENTRAL_BANK_RATE,8)
    def test_no_lookahead(self):
        s=pd.Series(np.arange(60,dtype=float),index=pd.period_range("2020-01",periods=60,freq="M"))
        a=forecast(s)
        s.iloc[-12]=10000
        b=forecast(s)
        self.assertEqual(a.iloc[0].AR1,b.iloc[0].AR1)
    def test_end_to_end_synthetic(self):
        rng=np.random.default_rng(42)
        dates=pd.period_range("2016-11","2026-09",freq="M")
        n=len(dates)
        df=pd.DataFrame({"DATE":dates.astype(str),"CBR":9+rng.normal(0,1,n),"LENDING":13+rng.normal(0,1,n),"INFLATION_YOY":5+rng.normal(0,1,n)})
        p,_=prepare([df])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"panel.csv"
            p.to_csv(path)
            result=analyze(load_panel(path),Path(folder)/"out")
            self.assertEqual(len(result),2)
            self.assertTrue((Path(folder)/"out/tables/forecast_metrics.csv").exists())
            p.iloc[0,0]=np.nan
            p.to_csv(path)
            with self.assertRaises(ValueError):
                load_panel(path)
