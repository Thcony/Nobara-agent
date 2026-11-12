import subprocess

READONLY = (
    "ls", "cat", "head", "tail", "grep", "rg", "journalctl", "dmesg",
    "systemctl status", "systemctl list", "rpm -qa", "rpm -qi", "dnf list",
    "dnf info", "dnf search", "which", "whereis", "ps", "free", "df", "du",
    "uptime", "uname", "echo", "wc", "find", "file", "id", "whoami", "date",
    "stat", "hostname", "lspci", "lsusb", "lsblk", "env", "printenv", "pwd",
    "git status", "git log", "git diff", "ping", "ip a", "ss -",
)


def is_readonly(cmd: str) -> bool:
    c = cmd.strip()
    return any(c.startswith(p) for p in READONLY)


def handle_shell(cmd: str) -> dict:
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=90
        )
        out = proc.stdout or ""
        if proc.stderr:
            out += "\n[stderr] " + proc.stderr
        return {"output": out[-8000:], "returncode": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"error": "comando excedeu o tempo limite de 90s"}
    except Exception as e:
        return {"error": str(e)}
