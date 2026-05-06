import os
import subprocess
import tempfile
import json
import ast


def get_function_at_line(code, line_number):
    """Find which function contains the given line and return full function code."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.lineno <= line_number <= node.end_lineno:
                    lines = code.split("\n")
                    func_lines = lines[node.lineno - 1:node.end_lineno]
                    return {
                        "name": node.name,
                        "start_line": node.lineno,
                        "end_line": node.end_lineno,
                        "code": "\n".join(func_lines)
                    }
    except:
        pass
    return None


def run_bandit(code):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    result = subprocess.run(
        ["bandit", "-f", "json", "-ll", tmp_path],
        capture_output=True, text=True
    )
    os.unlink(tmp_path)

    lines = code.split("\n")

    try:
        data = json.loads(result.stdout)
        findings = []
        for issue in data.get("results", []):
            line_num = issue["line_number"]
            actual_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""
            func_info = get_function_at_line(code, line_num)

            findings.append({
                "line": line_num,
                "actual_code": actual_line,
                "function_name": func_info["name"] if func_info else "module level",
                "function_code": func_info["code"] if func_info else actual_line,
                "function_start_line": func_info["start_line"] if func_info else line_num,
                "issue": issue["issue_text"],
                "severity": issue["issue_severity"],
                "confidence": issue["issue_confidence"],
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

    lines = code.split("\n")

    try:
        data = json.loads(result.stdout)
        findings = []
        for issue in data:
            line_num = issue["location"]["row"]
            actual_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""
            func_info = get_function_at_line(code, line_num)

            findings.append({
                "line": line_num,
                "actual_code": actual_line,
                "function_name": func_info["name"] if func_info else "module level",
                "function_code": func_info["code"] if func_info else actual_line,
                "function_start_line": func_info["start_line"] if func_info else line_num,
                "col": issue["location"]["column"],
                "code": issue["code"],
                "issue": issue["message"],
                "fix_available": issue.get("fix") is not None,
                "fix_ref": f"https://docs.astral.sh/ruff/rules/{issue['code'].lower()}"
            })
        return findings
    except:
        return []


def analyze_file(filename, file_info):
    code = file_info["code"]
    ext = file_info["ext"]

    bandit_findings = []
    ruff_findings = []

    if ext == ".py":
        bandit_findings = run_bandit(code)
        ruff_findings = run_ruff(code)

    return bandit_findings, ruff_findings


def chunk_files(file_contents, chunk_size=5):
    items = list(file_contents.items())
    return [dict(items[i:i+chunk_size]) for i in range(0, len(items), chunk_size)]