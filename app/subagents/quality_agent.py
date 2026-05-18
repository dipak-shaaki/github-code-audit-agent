import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import run_ruff,run_semgrep


def analyze_quality(files):
    """
    Quality Subagent's one job: find code quality issues.
    
    How it works:
    1. Receives dict of filename -> file_info
    2. Runs Ruff on Python files only
       (catches: unused variables, bad style, complexity,
        missing imports, dead code, formatting issues)
    3. Returns quality findings per file
    
    Why only Python?
    Ruff is a Python-specific linter. For JS/TS quality
    you would use ESLint — future addition.
    
    Example output:
    {
        "app/main.py": [
            {line: 5, issue: "unused variable", code: "F841"}
        ]
    }
    """
    findings = {}

    for filename, file_info in files.items():
        ext = file_info["ext"]
        code = file_info["code"]

        ruff_results = []
        semgrep_results = []

        # ruff only works on Python files
        if ext == ".py":
            ruff_results = run_ruff(code)
            if ruff_results:
                findings[filename] = ruff_results

        semgrep_results = run_semgrep(code, ext)
        
        if ruff_results or semgrep_results:
            findings[filename] = {
                "ruff": ruff_results,
                "semgrep": semgrep_results
            }

    return findings