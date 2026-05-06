import os
import requests
import ast

SONARCLOUD_TOKEN = os.getenv("SONARCLOUD_TOKEN")
SONARCLOUD_ORG = os.getenv("SONARCLOUD_ORG")
SONARCLOUD_PROJECT = os.getenv("SONARCLOUD_PROJECT")

BASE_URL = "https://sonarcloud.io/api"

def get_sonar_issues(pr_number=None):
    """Fetch issues from SonarCloud for a project."""
    
    params = {
        "organization": SONARCLOUD_ORG,
        "componentKeys": SONARCLOUD_PROJECT,
        "resolved": "false",
        "ps": 100  # page size max 100 issues
    }
    
    # if PR number provided  fetch only PR-specific issues
    if pr_number:
        params["pullRequest"] = pr_number
    
    response = requests.get(
        f"{BASE_URL}/issues/search",
        headers={"Authorization": f"Bearer {SONARCLOUD_TOKEN}"},
        params=params
    )
    
    if response.status_code != 200:
        print(f"  SonarCloud API error: {response.status_code}")
        return []
    
    data = response.json()
    findings = []
    
    for issue in data.get("issues", []):
        findings.append({
            "file": issue.get("component", "").split(":")[-1],
            "line": issue.get("line", 0),
            "type": issue.get("type"),           # BUG, VULNERABILITY, CODE_SMELL
            "severity": issue.get("severity"),   # BLOCKER, CRITICAL, MAJOR, MINOR
            "message": issue.get("message"),
            "rule": issue.get("rule"),
            "effort": issue.get("effort"),       # fix effort estimate
        })
    
    return findings



def get_function_at_line(code, line_number):
    tree = ast.parse(code)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # check if line_number falls inside this function
            if node.lineno <= line_number <= node.end_lineno:
                # extract those lines from code
                lines = code.split("\n")
                func_lines = lines[node.lineno - 1:node.end_lineno]
                return {
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "code": "\n".join(func_lines)
                }
    
    return None