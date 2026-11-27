"""Generate descriptive charts from the collected commercial bank snapshot."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.prepare import prepare

def main():
    data=pd.read_csv("data/raw/commercial_bank_snapshot_2026.csv")
    panel,conflicts=prepare([data],"2026-01","2026-09")
    folder=Path("outputs/figures")
    folder.mkdir(parents=True,exist_ok=True)
    for columns,name,title in [
        (["LENDING","OVERDRAFT"],"commercial_credit_rates","Kenya commercial bank credit rates"),
        (["DEPOSIT","SAVINGS"],"commercial_deposit_rates","Kenya deposit and savings rates")]:
        ax=panel[columns].to_timestamp().plot(marker="o",figsize=(10,5),grid=True)
        ax.set(title=title+" | Jan–Sep 2026",ylabel="Rate (%)",xlabel="Month")
        ax.figure.text(.1,.01,"Source: CBK, collected 27 Nov 2026. Conflicting observations withheld.")
        ax.figure.tight_layout(rect=[0,.05,1,1])
        ax.figure.savefig(folder/(name+".png"),dpi=160)
        plt.close(ax.figure)
if __name__=="__main__":
    main()
