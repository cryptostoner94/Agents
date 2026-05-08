import subprocess, textwrap, uuid
from pathlib import Path
 
BASE = Path("/opt/nexus-omega")
SANDBOX = BASE / "state" / "sandbox"
SANDBOX.mkdir(parents=True, exist_ok=True)
FORBIDDEN = ["import os", "subprocess", "socket", "shutil.rmtree", "open('/", 'open("/']
 
def run_python(code: str, timeout: int = 8):
    low = code.lower()
    for item in FORBIDDEN:
        if item in low:
            return {"ok": False, "error": f"blocked unsafe code pattern: {item}"}
    job = SANDBOX / f"code_{uuid.uuid4().hex}.py"
    job.write_text(textwrap.dedent(code), encoding="utf-8")
    try:
        p = subprocess.run(["python3", str(job)], cwd=str(SANDBOX), text=True, capture_output=True, timeout=timeout)
        return {"ok": p.returncode == 0, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:], "returncode": p.returncode, "file": str(job)}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "sandbox timeout", "file": str(job)}
