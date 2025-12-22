import subprocess
from pathlib import Path

# get changed python files in PR
try:
    files = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=AM", "HEAD~1"]
    ).decode().splitlines()
except Exception:
    files = []

py_files = [f for f in files if f.endswith(".py")]

if not py_files:
    print("✅ No Python files changed")
    exit(0)

print("🛠️ Code Review Report\n")

for file in py_files:
    path = Path(file)
    if not path.exists():
        continue

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assigned = {}
    used = set()

    for i, line in enumerate(lines, start=1):
        if "=" in line:
            left, right = line.split("=", 1)
            left = left.strip()
            if left.isidentifier():
                assigned[left] = i
            for w in right.split():
                if w.isidentifier():
                    used.add(w)
        else:
            for w in line.split():
                if w.isidentifier():
                    used.add(w)

    for var, ln in assigned.items():
        if var not in used:
            print(f"{file}: ❌ BUG `{var}` unused at line {ln}")
