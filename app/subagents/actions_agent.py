import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import run_semgrep


def analyze_github_actions(files):
    """
    GitHub Actions Subagent — one job: find workflow vulnerabilities.
    
    How it works:
    1. Filters for .yml and .yaml files only
    2. Runs Semgrep with yaml rules
    3. Semgrep has specific GitHub Actions rules that catch:
       - Injection via ${{ github.event.* }} in run: commands
       - Untrusted input passed to shell
       - Missing permission restrictions
       - Use of pull_request_target with checkout (dangerous)
       - Hardcoded secrets in env: blocks
    
    Example vulnerability it catches:
    
    BAD:
        - name: Print title
          run: echo "${{ github.event.issue.title }}"
          # attacker controls issue title — shell injection
    
    GOOD:
        - name: Print title
          env:
            TITLE: ${{ github.event.issue.title }}
          run: echo "$TITLE"
          # input sanitized via environment variable
    
    Example output:
    {
        ".github/workflows/ci.yml": [
            {
                line: 12,
                issue: "Untrusted input in run step",
                rule_id: "github-actions.injection",
                severity: "ERROR"
            }
        ]
    }
    """
    findings = {}

    for filename, file_info in files.items():
        ext = file_info["ext"]
        code = file_info["code"]

        # only process YAML files
        if ext in [".yml", ".yaml"]:
            semgrep_results = run_semgrep(code, ext)
            if semgrep_results:
                findings[filename] = semgrep_results

    return findings