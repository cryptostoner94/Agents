BLOCKED = [
    "seed phrase","private key","wallet password","exchange login","kyc",
    "credit card","malware","ransomware","phishing","steal","exfiltrate",
    "ddos","credential dump","crypto miner","xmrig"
]
 
SAFE_SHELL_PREFIXES = [
    "pwd", "ls", "date", "whoami",
    "curl http://127.0.0.1:8000/health",
    "systemctl status nexus-omega",
    "systemctl restart nexus-omega",
    "journalctl -u nexus-omega"
]
 
def check_text(text: str):
    low = (text or "").lower()
    for term in BLOCKED:
        if term in low:
            return False, f"blocked unsafe request: {term}"
    return True, "ok"
 
def shell_allowed(command: str):
    command = (command or "").strip()
    return any(command.startswith(prefix) for prefix in SAFE_SHELL_PREFIXES)
