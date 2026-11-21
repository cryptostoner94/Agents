import os
import subprocess
from core.policy import shell_argv

def run_shell(command: str):
    argv = shell_argv(command)
    if argv is None:
        return {"ok": False, "error": "command blocked by allowlist", "command": command}
    p = subprocess.run(list(argv), shell=False, text=True, capture_output=True, timeout=20)
    return {"ok": p.returncode == 0, "command": command, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:], "returncode": p.returncode}
