import subprocess
from core.policy import shell_allowed
 
def run_shell(command: str):
    if not shell_allowed(command):
        return {"ok": False, "error": "command blocked by allowlist", "command": command}
    p = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=20)
    return {"ok": p.returncode == 0, "command": command, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:], "returncode": p.returncode}
