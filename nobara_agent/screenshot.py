import os
import shutil
import subprocess

CANDIDATES = [
    ["spectacle", "-b", "-n", "-o", "{path}"],
    ["gnome-screenshot", "-f", "{path}"],
    ["grim", "{path}"],
    ["maim", "{path}"],
    ["import", "-window", "root", "{path}"],
    ["scrot", "{path}"],
]


def capture_screen(path: str = "/tmp/nobara_agent_screen.png"):
    for argv in CANDIDATES:
        if not shutil.which(argv[0]):
            continue
        try:
            subprocess.run(
                [a.replace("{path}", path) for a in argv],
                check=True, timeout=15,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return path
        except Exception:
            continue
    return None
