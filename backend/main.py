from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# -------- ENABLE CORS --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all origins (safe for local dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- DATA MODEL --------
class CodeInput(BaseModel):
    code: str

@app.get("/")
def home():
    return {"message": "Code Review Tool Backend Running"}

@app.post("/analyze")
def analyze_code(input: CodeInput):
    code = input.code
    issues = []

    lines = code.split("\n")

    if "print(" in code:
        issues.append({
            "type": "warning",
            "message": "Avoid using print() in production code"
        })

    if len(lines) > 30:
        issues.append({
            "type": "warning",
            "message": "File is long. Consider breaking code into smaller functions"
        })

    assigned = set()
    used = set()

    for line in lines:
        if "=" in line:
            left = line.split("=")[0].strip()
            if left.isidentifier():
                assigned.add(left)

        for word in line.split():
            if word.isidentifier():
                used.add(word)

    unused_vars = assigned - used
    for var in unused_vars:
        issues.append({
            "type": "bug",
            "message": f"Variable '{var}' is assigned but never used"
        })

    if not issues:
        issues.append({
            "type": "info",
            "message": "No obvious issues found"
        })

    return {"issues": issues}
