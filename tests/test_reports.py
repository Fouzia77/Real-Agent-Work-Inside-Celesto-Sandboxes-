
import json, math, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"^sbx-[a-z0-9]{8,}$")

def read_json(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def test_problem_report():
    x=read_json("reports/problem.json")
    assert len(x["who"])>=40 and len(x["agent_work"])>=40 and len(x["proof_output"])>=20
    assert x["idea_source"] in {"idea_bank","original"}

def test_capabilities_and_evidence():
    x=read_json("reports/capabilities.json")["capabilities"]
    assert len(x)>=2
    assert len({a["id"] for a in x})==len(x)
    for a in x:
        assert len(a["why"])>=80
        assert (ROOT/a["evidence_path"]).exists()

def test_lifecycle():
    x=read_json("reports/lifecycle.json")
    assert all(x[k] is True for k in ["cleanup_on_success","cleanup_on_failure","cleanup_on_interrupt"])
    assert len(x["sandbox_names"])==len(set(x["sandbox_names"]))>0
    assert all(NAME.fullmatch(n) for n in x["sandbox_names"])

def test_command_log():
    rows=[json.loads(line) for line in (ROOT/"logs/commands.jsonl").read_text().splitlines() if line.strip()]
    assert rows
    for r in rows:
        assert r["decision"] in {"allow","block"}
        assert r["execution_target"]=="celesto_sandbox"
        assert NAME.fullmatch(r["sandbox_name"])
        assert r["command"] and "ts" in r

def test_reliability_math_and_unique_fresh_runs():
    x=read_json("reports/reliability.json")
    runs=x["runs"]; n=len(runs)
    assert n>=20 and x["run_count"]==n
    assert all(r["fresh"] is True and NAME.fullmatch(r["sandbox_name"]) for r in runs)
    assert len({r["sandbox_name"] for r in runs})==n
    assert runs==sorted(runs,key=lambda r:r["wall_clock_s"])
    assert abs(x["success_rate"]-sum(r["success"] for r in runs)/n)<.001
    walls=sorted(r["wall_clock_s"] for r in runs)
    median=(walls[(n-1)//2]+walls[n//2])/2
    assert abs(x["median_wall_clock_s"]-median)<.001
    assert abs(x["p90_wall_clock_s"]-walls[math.ceil(.9*n)-1])<.001
    boots=sorted(r["boot_to_ready_s"] for r in runs)
    assert abs(x["median_boot_to_ready_s"]-(boots[(n-1)//2]+boots[n//2])/2)<.001
    assert abs(x["total_cost_usd"]-sum(r["cost_usd"] for r in runs))<.01
    assert len((ROOT/x["postmortem_path"]).read_text())>=200

def test_containment():
    x=read_json("reports/containment.json")
    assert x["attack"] in {"prompt_injection_exfil","destructive_command","suspicious_package"}
    assert x["blocked"] is True and x["host_untouched"] is True
    assert x["evidence_paths"] and all((ROOT/p).exists() for p in x["evidence_paths"])

def test_failure_policy_trace():
    x=read_json("reports/failure_policy.json")
    assert x["failed_step"]==7 and x["total_steps"]==10
    assert x["policy"] in {"resume","rollback","fresh"} and len(x["rationale"])>=200
    rows=[json.loads(l) for l in (ROOT/x["trace_path"]).read_text().splitlines() if l.strip()]
    assert any(r.get("event")=="policy_applied" and r.get("policy")==x["policy"] for r in rows)

def test_concurrency():
    x=read_json("reports/concurrency.json")
    assert len(x["jobs"])>=5 and len({j["sandbox_name"] for j in x["jobs"]})==len(x["jobs"])
    assert all(NAME.fullmatch(j["sandbox_name"]) and j["started_at"] for j in x["jobs"])
    assert len(x["breakage_notes"])>=40

def test_readme_required_phrases():
    x=(ROOT/"README.md").read_text()
    for phrase in ["Problem statement","How I used Celesto","Eval report","Containment test","State and failure design","Setup"]:
        assert phrase.lower() in x.lower()
