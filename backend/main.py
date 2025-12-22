from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# -------- ENABLE CORS --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- DATA MODEL --------
class CodeInput(BaseModel):
    code: str

# -------- HOME --------
@app.get("/")
def home():
    return {"message": "Code Review Tool Backend Running"}

# -------- ANALYZE --------
@app.post("/analyze")
def analyze_code(input: CodeInput):
    code = input.code
    issues = []

    lines = code.split("\n")

    # ---------- RULE 1: print() usage ----------
    for i, line in enumerate(lines, start=1):
        if "print(" in line:
            issues.append({
                "severity": "WARNING",
                "line": i,
                "message": "Avoid using print() in production code"
            })

    # ---------- RULE 2: file too long ----------
    if len(lines) > 30:
        issues.append({
            "severity": "INFO",
            "line": None,
            "message": "File is long. Consider breaking code into smaller functions"
        })

    # ---------- RULE 3: UNUSED VARIABLES (CORRECT LOGIC) ----------
    assigned = {}   # variable -> line number
    used = set()    # variables used on RHS or later lines

    for i, line in enumerate(lines, start=1):
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" in line:
            left, right = line.split("=", 1)
            left = left.strip()

            # assignment
            if left.isidentifier():
                assigned[left] = i

            # usage on RHS
            for word in right.replace("(", " ").replace(")", " ").split():
                if word.isidentifier():
                    used.add(word)
        else:
            # usage in non-assignment lines
            for word in line.replace("(", " ").replace(")", " ").split():
                if word.isidentifier():
                    used.add(word)

    for var, line_no in assigned.items():
        if var not in used:
            issues.append({
                "severity": "BUG",
                "line": line_no,
                "message": f"Variable '{var}' is assigned but never used"
            })

    # ---------- NO ISSUES ----------
    if not issues:
        issues.append({
            "severity": "INFO",
            "line": None,
            "message": "No obvious issues found"
        })

    return {"issues": issues}
