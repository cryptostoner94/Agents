import shlex

BLOCKED = [
    "seed phrase","private key","wallet password","exchange login","kyc",
    "credit card","malware","ransomware","phishing","steal","exfiltrate",
    "ddos","credential dump","crypto miner","xmrig"
]

SAFE_SHELL_COMMANDS = [
    ("pwd",),
    ("ls",),
    ("date",),
    ("whoami",),
    ("curl", "http://127.0.0.1:8000/health"),
    ("systemctl", "status", "nexus-omega"),
    ("systemctl", "restart", "nexus-omega"),
    ("journalctl", "-u", "nexus-omega"),
]

def check_text(text: str):
    low = (text or "").lower()
    for term in BLOCKED:
        if term in low:
            return False, f"blocked unsafe request: {term}"
    return True, "ok"

def shell_argv(command: str):
    """Return the argv tuple for an allowlisted command, else None.

    The command is split into arguments without shell expansion and must equal
    one allowlisted vector exactly, so "ls; id" and "ls $(id)" are rejected.
    """
    try:
        argv = shlex.split(command or "", posix=True)
    except ValueError:
        return None
    argv = tuple(argv)
    return argv if argv in SAFE_SHELL_COMMANDS else None

def shell_allowed(command: str):
    return shell_argv(command) is not None
