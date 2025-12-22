# code-review-tool
This is where i will be sharing the steps of my code review tool that i am making for my project
# 🛠️ Code Review Tool (Python)

An automated **Python static code analysis tool** with a **web interface** and **GitHub Actions integration** that reviews code for common bugs and style issues.

This project is designed to simulate **real-world code review workflows** used in software teams.

---

## 🚀 Features

### ✅ Static Code Analysis
- Detects **unused variables**
- Warns about `print()` usage
- File length checks
- Line numbers & severity levels (BUG / WARNING / INFO)

### 🌐 Web Interface
- Paste Python code and analyze instantly
- Upload `.py` files for analysis
- Clean, color-coded results with line numbers

### 🤖 GitHub Actions (CI/CD)
- Automatically runs on **Pull Requests**
- Reviews Python files during PR
- Reports issues directly in CI logs

### 🧹 Clean Repository
- `.gitignore` configured
- No generated files (`__pycache__`, `.pyc`) tracked

---

## 🧱 Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** HTML, CSS, JavaScript
- **Static Analysis:** Custom Python logic
- **CI/CD:** GitHub Actions
- **Version Control:** Git & GitHub

---

## 📂 Project Structure

code-review-tool/
├── backend/
│ ├── main.py
│ └── requirements.txt
├── frontend/
│ └── index.html
├── .github/
│ └── workflows/
│ └── code-review.yml
├── ci_review.py
├── .gitignore
└── README.md

yaml
Copy code

---

## 🧪 How It Works

### Web App
1. User pastes code or uploads a `.py` file
2. Backend analyzes code using static rules
3. Issues are returned with:
   - Severity
   - Line number
   - Explanation

### GitHub Action
1. Pull Request is opened
2. GitHub Action runs automatically
3. `ci_review.py` checks changed Python files
4. Issues are reported in CI logs

---

## ▶️ Run Locally

### 1️⃣ Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
Backend runs at:

cpp
Copy code
http://127.0.0.1:8000
2️⃣ Frontend
Open this file directly in browser:

bash
Copy code
frontend/index.html
🧩 Example Issues Detected
python
Copy code
x = 10
print("hello")
Output:

pgsql
Copy code
BUG      Line 1 → Variable 'x' is assigned but never used
WARNING  Line 2 → Avoid using print() in production code
🧠 Learning Outcomes
Built a custom static analysis engine

Integrated CI/CD using GitHub Actions

Learned real-world PR automation workflows

Understood code quality & repository hygiene

🔮 Future Improvements
AST-based analysis (functions too long, nested loops)

AI-based explanations for detected issues

Multi-language support (Java, C++)

Inline PR comments instead of logs

Online deployment

👤 Author
Prash-2402
B.Tech CSE (AI & ML)
Focused on Backend, Automation & AI-assisted tooling

⭐ Why This Project Matters
This tool demonstrates:

Real software engineering practices

Automation mindset

Practical GitHub usage

Internship-ready skills

⭐ Star the repo if you find it useful!

yaml
Copy code

---

## ✅ WHAT TO DO NOW
1️⃣ Paste this into `README.md`  
2️⃣ Commit it:
```bash
git add README.md
git commit -m "add project README"
git push