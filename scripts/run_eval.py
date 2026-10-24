
"""Run 20 real end-to-end Celesto guest jobs and replace the fixture report with measured data.

Requires CELESTO_PROVIDER=cloud and CELESTO_API_KEY. This intentionally refuses to label
simulated/local API checks as real sandbox evaluations.
"""
import json, statistics, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.agent import run_proof_task

def main(n=20):
    import os
    if os.getenv("CELESTO_PROVIDER","cloud") != "cloud" or not os.getenv("CELESTO_API_KEY") or os.getenv("CELESTO_API_KEY")=="replace-me":
        raise SystemExit("Set CELESTO_PROVIDER=cloud and a real CELESTO_API_KEY in .env before running live evaluations.")
    runs=[]
    for i in range(n):
        print(f"[{i+1}/{n}] starting fresh Celesto guest...", flush=True)
        r=run_proof_task(provider="cloud")
        runs.append({"sandbox_name":r["sandbox_name"],"fresh":True,"success":bool(r["success"]),
                     "wall_clock_s":round(r["wall_clock_s"],4),
                     "boot_to_ready_s":round(r["boot_to_ready_s"],4),
                     "cost_usd":round(float(os.getenv("CELESTO_MICRO_HOURLY_USD","0.015"))*r["wall_clock_s"]/3600,6)})
    runs.sort(key=lambda x:x["wall_clock_s"])
    walls=[x["wall_clock_s"] for x in runs]; boots=sorted(x["boot_to_ready_s"] for x in runs)
    n=len(runs)
    median=lambda a:(a[(n-1)//2]+a[n//2])/2
    report={"evaluation_mode":"live_celesto_cloud","run_count":n,"runs":runs,
            "success_rate":sum(x["success"] for x in runs)/n,
            "median_wall_clock_s":median(walls),"p90_wall_clock_s":walls[__import__("math").ceil(.9*n)-1],
            "median_boot_to_ready_s":median(boots),"total_cost_usd":round(sum(x["cost_usd"] for x in runs),6),
            "postmortem_path":"reports/postmortem.md"}
    (ROOT/"reports/reliability.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="runs"},indent=2))
if __name__=="__main__":
    main(int(sys.argv[1]) if len(sys.argv)>1 else 20)
