import os
import subprocess
import tempfile

def run_bandit(code):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    result = subprocess.run(
        ["bandit", "-f", "json", "-ll", tmp_path],
        capture_output=True, text=True
    )
    os.unlink(tmp_path)
    
    import json
    try:
        data = json.loads(result.stdout)
        findings = []
        for issue in data.get("results", []):
            findings.append({
                "line": issue["line_number"],
                "issue": issue["issue_text"],
                "severity": issue["issue_severity"],
                "confidence": issue["issue_confidence"],
                "code": issue["code"],
                "fix_ref": issue["more_info"]
            })
        return findings
    except:
        return []

def run_ruff(code):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    result = subprocess.run(
        ["ruff", "check", "--output-format", "json", tmp_path],
        capture_output=True, text=True
    )
    os.unlink(tmp_path)

    import json
    try:
        data = json.loads(result.stdout)
        findings = []
        for issue in data:
            findings.append({
                "line": issue["location"]["row"],
                "col": issue["location"]["column"],
                "code": issue["code"],
                "issue": issue["message"],
                "fix_available": issue.get("fix") is not None,
                "fix_ref": f"https://docs.astral.sh/ruff/rules/{issue['code'].lower()}"
            })
        return findings
    except:
        return []

# def run_semgrep(code, ext):
#     # map extension to semgrep language
#     lang_map = {
#         ".py": "python",
#         ".js": "javascript",
#         ".ts": "typescript",
#         ".java": "java",
#         ".go": "go",
#         ".rb": "ruby",
#         ".sql": "sql",
#     }
    
#     lang = lang_map.get(ext)
#     if not lang:
#         return "No semgrep support for this file type."

#     with tempfile.NamedTemporaryFile(suffix=ext, mode="w", delete=False) as tmp:
#         tmp.write(code)
#         tmp_path = tmp.name

#     result = subprocess.run(
#         [
#             "semgrep",
#             "--config", "auto",  # auto picks best rules for the language
#             "--json",
#             tmp_path
#         ],
#         capture_output=True, text=True
#     )
#     os.unlink(tmp_path)
#     return result.stdout


def analyze_file(filename, file_info):
    code = file_info["code"]
    ext = file_info["ext"]

    bandit_findings = []
    ruff_findings = []

    if ext == ".py":
        bandit_findings = run_bandit(code)
        ruff_findings = run_ruff(code)
    
    return bandit_findings, ruff_findings