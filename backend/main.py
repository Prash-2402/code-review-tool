from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import ast

app = FastAPI()

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DATA MODEL ----------
class CodeInput(BaseModel):
    code: str

# ---------- HOME ----------
@app.get("/")
def home():
    return {"message": "Code Review Tool Backend Running"}

# ---------- CORE ANALYSIS ----------
def analyze_text(code: str):
    issues = []
    lines = code.split("\n")

    # ---------- RULE 1: print() ----------
    for i, line in enumerate(lines, start=1):
        if "print(" in line:
            issues.append({
                "severity": "WARNING",
                "line": i,
                "message": "Avoid using print() in production code"
            })

    # ---------- RULE 2: FILE TOO LONG ----------
    if len(lines) > 30:
        issues.append({
            "severity": "INFO",
            "line": None,
            "message": "File is long. Consider breaking code into smaller functions"
        })

    # ---------- RULE 3: UNUSED VARIABLES ----------
    assigned = {}
    used = set()

    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" in line:
            left, right = line.split("=", 1)
            left = left.strip()

            if left.isidentifier():
                assigned[left] = i

            for word in right.replace("(", " ").replace(")", " ").split():
                if word.isidentifier():
                    used.add(word)
        else:
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

    # ---------- RULE 4: FUNCTION TOO LONG (AST) ----------
    try:
        tree = ast.parse(code)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start = node.lineno
                end = max(
                    getattr(n, "lineno", start)
                    for n in ast.walk(node)
                )
                length = end - start + 1

                if length > 15:
                    issues.append({
                        "severity": "WARNING",
                        "line": start,
                        "message": f"Function '{node.name}' is too long ({length} lines). Consider refactoring."
                    })
    except SyntaxError:
        issues.append({
            "severity": "ERROR",
            "line": None,
            "message": "Syntax error detected. Unable to analyze functions."
        })

    # ---------- NO ISSUES ----------
    if not issues:
        issues.append({
            "severity": "INFO",
            "line": None,
            "message": "No obvious issues found"
        })

    return {"issues": issues}

# ---------- TEXT INPUT ----------
@app.post("/analyze")
def analyze_code(input: CodeInput):
    return analyze_text(input.code)

# ---------- FILE UPLOAD ----------
@app.post("/analyze-file")
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".py"):
        return {
            "issues": [{
                "severity": "ERROR",
                "line": None,
                "message": "Only .py files are supported"
            }]
        }

    content = await file.read()
    code = content.decode("utf-8")
    return analyze_text(code)
