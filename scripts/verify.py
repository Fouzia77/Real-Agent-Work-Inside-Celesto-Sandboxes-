
"""Fast offline structural verification for submission artifacts."""
import json, re, math
from pathlib import Path
R=Path(__file__).resolve().parents[1]
NAME=re.compile(r"^sbx-[a-z0-9]{8,}$")
errors=[]
def need(ok,msg):
    if not ok: errors.append(msg)
def j(p): return json.loads((R/p).read_text(encoding="utf-8"))
p=j("reports/problem.json")
need(len(p.get("who",""))>=40 and len(p.get("agent_work",""))>=40 and len(p.get("proof_output",""))>=20,"problem fields")
c=j("reports/capabilities.json")["capabilities"]
need(len(c)>=2,"at least two capabilities")
for x in c: need(len(x["why"])>=80 and (R/x["evidence_path"]).exists(),"capability evidence/why")
l=j("reports/lifecycle.json")
need(all(l.get(k) is True for k in ("cleanup_on_success","cleanup_on_failure","cleanup_on_interrupt")),"lifecycle flags")
rr=j("reports/reliability.json"); runs=rr["runs"]; n=len(runs)
need(n>=20 and n==rr["run_count"],"reliability run count")
need(len({x["sandbox_name"] for x in runs})==n and all(x["fresh"] and NAME.fullmatch(x["sandbox_name"]) for x in runs),"fresh unique names")
need(runs==sorted(runs,key=lambda x:x["wall_clock_s"]),"runs must be sorted")
if n:
    w=sorted(x["wall_clock_s"] for x in runs); b=sorted(x["boot_to_ready_s"] for x in runs)
    med=lambda a:(a[(n-1)//2]+a[n//2])/2
    need(abs(rr["success_rate"]-sum(x["success"] for x in runs)/n)<.001,"success rate mismatch")
    need(abs(rr["median_wall_clock_s"]-med(w))<.001,"median mismatch")
    need(abs(rr["p90_wall_clock_s"]-w[math.ceil(.9*n)-1])<.001,"p90 mismatch")
    need(abs(rr["median_boot_to_ready_s"]-med(b))<.001,"boot median mismatch")
    need(abs(rr["total_cost_usd"]-sum(x["cost_usd"] for x in runs))<.01,"cost mismatch")
co=j("reports/containment.json")
need(co["blocked"] and co["host_untouched"] and all((R/x).exists() for x in co["evidence_paths"]),"containment evidence")
f=j("reports/failure_policy.json")
trace=[json.loads(x) for x in (R/f["trace_path"]).read_text().splitlines() if x.strip()]
need(any(x.get("event")=="policy_applied" and x.get("policy")==f["policy"] for x in trace),"failure trace")
con=j("reports/concurrency.json")
need(len(con["jobs"])>=5 and len({x["sandbox_name"] for x in con["jobs"]})==len(con["jobs"]),"concurrency")
need(not (R/".env").exists(),".env must not be submitted")
if errors:
    print("FAILED:")
    print("\n".join("- "+x for x in errors))
    raise SystemExit(1)
print("PASS: structural report checks. Note: live Celesto evaluation is separate; see README.")
