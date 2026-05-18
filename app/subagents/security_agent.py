import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import run_bandit, run_semgrep


def analyze_security(files):
    """
    Security Subagent — one job: find security vulnerabilities.
    
    How it works:
    1. Receives dict of filename -> file_info
    2. Runs Bandit on Python files (catches: SQL injection, 
       hardcoded secrets, weak crypto, unsafe functions)
    3. Runs Semgrep on ALL files (catches: secrets in any language,
       injection patterns, dangerous functions)
    4. Returns combined security findings per file
    
    Example input:
    {
        "app/auth.py": {"code": "...", "ext": ".py"},
        "configs/settings.py": {"code": "...", "ext": ".py"}
    }
    
    Example output:
    {
        "app/auth.py": {
            "bandit": [{line, issue, severity, function_code}],
            "semgrep": [{line, issue, rule_id}]
        }
    }
    
    """
    findings = {}

    for filename, file_info in files.items():
        code = file_info["code"]
        ext = file_info["ext"]

        bandit_results = []
        semgrep_results = []

        # bandit only works on Python
        if ext == ".py":
            bandit_results = run_bandit(code)

        # semgrep works on everything
        semgrep_results = run_semgrep(code, ext)

        # only store if we found something
        if bandit_results or semgrep_results:
            findings[filename] = {
                "bandit": bandit_results,
                "semgrep": semgrep_results
            }

    return findings