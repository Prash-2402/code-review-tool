from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeInput(BaseModel):
    code: str

@app.get("/")
def home():
    return {"message": "Code Review Tool Backend Running"}

# ---------- CORE ANALYSIS LOGIC ----------
def analyze_text(code: str):
    issues = []
    lines = code.split("\n")

    # print() rule
    for i, line in enumerate(lines, start=1):
        if "print(" in line:
            issues.append({
                "severity": "WARNING",
                "line": i,
                "message": "Avoid using print() in production code"
            })

    # file too long
    if len(lines) > 30:
        issues.append({
            "severity": "INFO",
            "line": None,
            "message": "File is long. Consider breaking code into smaller functions"
        })

    # unused variables
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
