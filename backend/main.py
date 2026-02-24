from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ast
from collections import defaultdict

app = FastAPI(title="Code Review Tool", version="2.0.0")

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
    return {"message": "Code Review Tool Backend v2.0 Running"}

# ================================================================
# CORE ANALYSIS ENGINE
# ================================================================

MAGIC_NUMBER_WHITELIST = {0, 1, -1, 2, 100}

def analyze_text(code: str) -> dict:
    issues = []
    lines = code.splitlines()

    # ── TRY AST PARSE ──────────────────────────────────────────
    tree = None
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        issues.append({
            "severity": "ERROR",
            "line": e.lineno,
            "message": f"Syntax error: {e.msg}"
        })

    # ── RULE 1: print() usage (text-level, catches all) ─────────
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "print(" in line:
            issues.append({
                "severity": "WARNING",
                "line": i,
                "message": "Avoid using print() in production code — use logging instead"
            })

    # ── RULE 2: File too long ────────────────────────────────────
    if len(lines) > 200:
        issues.append({
            "severity": "WARNING",
            "line": None,
            "message": f"File is very long ({len(lines)} lines). Consider splitting into modules."
        })
    elif len(lines) > 80:
        issues.append({
            "severity": "INFO",
            "line": None,
            "message": f"File is {len(lines)} lines. Consider breaking into smaller functions."
        })

    if tree is None:
        # Can't do AST analysis on broken code
        return _build_response(issues, len(lines))

    # ── RULE 3: Unused variables (AST-based) ─────────────────────
    _check_unused_variables(tree, issues)

    # ── RULE 4: Function too long ─────────────────────────────────
    _check_function_length(tree, issues)

    # ── RULE 5: Bare except: ──────────────────────────────────────
    _check_bare_except(tree, issues)

    # ── RULE 6: Missing docstrings ────────────────────────────────
    _check_missing_docstrings(tree, issues)

    # ── RULE 7: Mutable default arguments ────────────────────────
    _check_mutable_defaults(tree, issues)

    # ── RULE 8: Magic numbers ─────────────────────────────────────
    _check_magic_numbers(tree, issues)

    # ── RULE 9: Deeply nested loops ──────────────────────────────
    _check_nested_loops(tree, issues)

    # ── RULE 10: Unused imports ──────────────────────────────────
    _check_unused_imports(tree, code, issues)

    # ── RULE 11: TODO / FIXME comments ───────────────────────────
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            upper = stripped.upper()
            if "TODO" in upper or "FIXME" in upper or "HACK" in upper:
                issues.append({
                    "severity": "INFO",
                    "line": i,
                    "message": f"Unresolved comment: {stripped}"
                })

    if not issues:
        issues.append({
            "severity": "INFO",
            "line": None,
            "message": "✅ No issues found — great code!"
        })

    return _build_response(issues, len(lines))


def _build_response(issues: list, line_count: int) -> dict:
    summary = {"bugs": 0, "warnings": 0, "info": 0, "errors": 0, "total": len(issues)}
    for issue in issues:
        sev = issue.get("severity", "")
        if sev == "BUG":
            summary["bugs"] += 1
        elif sev == "WARNING":
            summary["warnings"] += 1
        elif sev == "INFO":
            summary["info"] += 1
        elif sev == "ERROR":
            summary["errors"] += 1
    # Sort: ERROR → BUG → WARNING → INFO
    order = {"ERROR": 0, "BUG": 1, "WARNING": 2, "INFO": 3}
    issues.sort(key=lambda x: (order.get(x.get("severity", "INFO"), 3), x.get("line") or 9999))
    return {"issues": issues, "summary": summary}


# ── RULE HELPERS ──────────────────────────────────────────────────

def _check_unused_variables(tree: ast.AST, issues: list):
    """AST-based unused variable detection scoped to each function."""
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            continue
        # Collect assignments and usages within this scope
        assigned = {}  # name -> lineno
        used = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        assigned[target.id] = target.lineno
            elif isinstance(child, ast.AugAssign):
                if isinstance(child.target, ast.Name):
                    used.add(child.target.id)
            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                used.add(child.id)
        for var, lineno in assigned.items():
            if var not in used and var not in ("__all__", "__version__", "__author__"):
                issues.append({
                    "severity": "BUG",
                    "line": lineno,
                    "message": f"Variable '{var}' is assigned but never used"
                })


def _check_function_length(tree: ast.AST, issues: list):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = max(
                getattr(n, "lineno", start)
                for n in ast.walk(node)
            )
            length = end - start + 1
            if length > 50:
                issues.append({
                    "severity": "WARNING",
                    "line": start,
                    "message": f"Function '{node.name}' is very long ({length} lines). Refactor into smaller functions."
                })
            elif length > 20:
                issues.append({
                    "severity": "INFO",
                    "line": start,
                    "message": f"Function '{node.name}' is {length} lines — consider refactoring for readability."
                })


def _check_bare_except(tree: ast.AST, issues: list):
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append({
                "severity": "WARNING",
                "line": node.lineno,
                "message": "Bare 'except:' catches all exceptions including KeyboardInterrupt. Specify exception types."
            })


def _check_missing_docstrings(tree: ast.AST, issues: list):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)):
                kind = "Function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "Class"
                if not node.name.startswith("_"):  # Skip private/dunder
                    issues.append({
                        "severity": "INFO",
                        "line": node.lineno,
                        "message": f"{kind} '{node.name}' is missing a docstring"
                    })


def _check_mutable_defaults(tree: ast.AST, issues: list):
    MUTABLE_TYPES = (ast.List, ast.Dict, ast.Set)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if default and isinstance(default, MUTABLE_TYPES):
                    issues.append({
                        "severity": "BUG",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' uses a mutable default argument. Use None and assign inside the function."
                    })
                    break


def _check_magic_numbers(tree: ast.AST, issues: list):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if node.value not in MAGIC_NUMBER_WHITELIST and node.col_offset != -1:
                # Skip if inside an annotation or class body attribute
                issues.append({
                    "severity": "INFO",
                    "line": node.lineno,
                    "message": f"Magic number '{node.value}' detected. Consider using a named constant."
                })


def _check_nested_loops(tree: ast.AST, issues: list):
    def _loop_depth(node, depth=0):
        if isinstance(node, (ast.For, ast.While)):
            depth += 1
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            child_depth = _loop_depth(child, depth)
            max_depth = max(max_depth, child_depth)
        return max_depth

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            depth = _loop_depth(node)
            if depth >= 3:
                lineno = getattr(node, "lineno", None)
                issues.append({
                    "severity": "WARNING",
                    "line": lineno,
                    "message": f"Deeply nested loops detected (depth {depth}). Consider refactoring to reduce complexity."
                })


def _check_unused_imports(tree: ast.AST, code: str, issues: list):
    imported_names = {}  # alias -> lineno
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name.split(".")[0]
                imported_names[name] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                name = alias.asname if alias.asname else alias.name
                imported_names[name] = node.lineno

    # Collect all Name usages (excluding the import lines themselves)
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

    for name, lineno in imported_names.items():
        if name not in used_names:
            issues.append({
                "severity": "WARNING",
                "line": lineno,
                "message": f"Imported name '{name}' is never used"
            })


# ================================================================
# ENDPOINTS
# ================================================================

@app.post("/analyze")
def analyze_code(input: CodeInput):
    return analyze_text(input.code)


@app.post("/analyze-file")
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".py"):
        return {
            "issues": [{
                "severity": "ERROR",
                "line": None,
                "message": "Only .py files are supported"
            }],
            "summary": {"bugs": 0, "warnings": 0, "info": 0, "errors": 1, "total": 1}
        }
    content = await file.read()
    try:
        code = content.decode("utf-8")
    except UnicodeDecodeError:
        return {
            "issues": [{
                "severity": "ERROR",
                "line": None,
                "message": "File encoding not supported — please use UTF-8"
            }],
            "summary": {"bugs": 0, "warnings": 0, "info": 0, "errors": 1, "total": 1}
        }
    return analyze_text(code)


@app.post("/metrics")
def get_metrics(input: CodeInput):
    """Returns code metrics: lines, functions, classes, avg function length."""
    lines = input.code.splitlines()
    metrics = {
        "total_lines": len(lines),
        "blank_lines": sum(1 for l in lines if not l.strip()),
        "comment_lines": sum(1 for l in lines if l.strip().startswith("#")),
        "functions": 0,
        "classes": 0,
        "avg_function_length": 0,
        "imports": 0,
    }
    try:
        tree = ast.parse(input.code)
        func_lengths = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics["functions"] += 1
                start = node.lineno
                end = max(getattr(n, "lineno", start) for n in ast.walk(node))
                func_lengths.append(end - start + 1)
            elif isinstance(node, ast.ClassDef):
                metrics["classes"] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics["imports"] += 1
        if func_lengths:
            metrics["avg_function_length"] = round(sum(func_lengths) / len(func_lengths), 1)
    except SyntaxError:
        pass
    return metrics
