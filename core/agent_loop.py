import time, uuid
from pathlib import Path
from core.memory import log_event
from core.policy import check_text
from core.browser_operator import extract_page, extract_urls
from core.code_sandbox import run_python
from core.shell_runner import run_shell
 
BASE = Path("/opt/nexus-omega")
ART = BASE / "artifacts"
ART.mkdir(parents=True, exist_ok=True)
DEFAULT_RESEARCH = ["https://news.ycombinator.com", "https://github.com/trending"]
 
def score_text(text):
    low=(text or "").lower(); score=0; signals=[]
    rules={"hiring":["hiring","jobs","careers","recruiting"],"manual_work":["manual","spreadsheet","workflow","report","admin"],"automation_fit":["automation","agent","api","browser","data"],"revenue":["pricing","paid","sales","growth","customer"],"urgency":["urgent","delay","slow","cost","support"]}
    for label, words in rules.items():
        if any(w in low for w in words):
            score += 2; signals.append(label)
    return min(score,10), signals
 
def write_report(task_id, objective, ranked):
    path = ART / f"{task_id}.md"
    lines = ["# NEXUS OMEGA Execution Report","",f"Task: `{task_id}`","","## Objective",objective,"","## Ranked Signals","| Rank | Source | Score | Signals |","|---:|---|---:|---|"]
    for i, r in enumerate(ranked, 1):
        lines.append(f"| {i} | {r.get('source') or r.get('url')} | {r.get('score')} | {', '.join(r.get('signals', []))} |")
    lines += ["","## Decision","Fastest route: sell a 72-hour automation pilot to a service business with visible repetitive workflow pain.","","## Offer","$300-$750 fixed automation pilot.","","## 72-Hour Plan","1. Pick one niche.","2. Identify 20 public leads.","3. Send targeted audit offer.","4. Build one browser/API workflow.","5. Deliver report artifact.","6. Convert to monthly retainer."]
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
 
async def run_agent(objective: str):
    task_id = f"task_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    allowed, reason = check_text(objective)
    if not allowed:
        return {"ok": False, "blocked": True, "reason": reason, "task_id": task_id}
    log_event(task_id, "start", {"objective": objective})
    low = objective.lower(); urls = extract_urls(objective)
    if low.startswith("python:"):
        result = run_python(objective.split("python:",1)[1]); log_event(task_id, "codeact", result)
        return {"ok": True, "mode": "codeact", "task_id": task_id, "result": result}
    if low.startswith("shell:"):
        result = run_shell(objective.split("shell:",1)[1].strip()); log_event(task_id, "shell", result)
        return {"ok": True, "mode": "shell", "task_id": task_id, "result": result}
    if urls:
        result = await extract_page(urls[0]); log_event(task_id, "browser", result)
        return {"ok": True, "mode": "browser", "task_id": task_id, "result": result}
    ranked=[]; observations=[]
    for url in DEFAULT_RESEARCH:
        obs = await extract_page(url); observations.append(obs)
        score, signals = score_text(obs.get("text_preview", ""))
        ranked.append({"source": obs.get("title") or url, "url": url, "score": score, "signals": signals, "screenshot": obs.get("screenshot")})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    report = write_report(task_id, objective, ranked)
    final = {"objective": objective, "ranked": ranked, "pilot_offer": "$300-$750 automation pilot", "execution_plan": ["Pick one niche","Find 20 leads","Send outreach","Build proof workflow","Deliver markdown artifact","Convert to monthly retainer"], "artifact": report}
    log_event(task_id, "final", final)
    return {"ok": True, "mode": "react-agent", "task_id": task_id, "result": final, "raw_observations": observations}
