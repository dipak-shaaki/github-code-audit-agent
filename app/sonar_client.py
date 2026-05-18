import os
import requests

BASE_URL = "https://sonarcloud.io/api"


def get_sonar_issues(repo_name=None, pr_number=None):
    """
    Fetch issues from SonarCloud.
    repo_name — used to derive project key automatically
    pr_number — if provided, fetches PR specific issues only
    """
    token = os.getenv("SONARCLOUD_TOKEN")
    org = os.getenv("SONARCLOUD_ORG")

    if not token or not org:
        print("  SonarCloud not configured — skipping")
        return []

    # derive project key from repo name automatically
    if repo_name:
        project_key = repo_name.replace("/", "_")
    else:
        project_key = os.getenv("SONARCLOUD_PROJECT")

    if not project_key:
        print("  SonarCloud project key missing skipping")
        return []

    params = {
        "organization": org,
        "componentKeys": project_key,
        "resolved": "false",
        "ps": 100
    }

    if pr_number:
        params["pullRequest"] = pr_number

    try:
        response = requests.get(
            f"{BASE_URL}/issues/search",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10
        )

        if response.status_code == 401:
            print("  SonarCloud: Invalid token — check SONARCLOUD_TOKEN in .env")
            return []
        elif response.status_code == 404:
            print(f"  SonarCloud: Project '{project_key}' not found — not connected to SonarCloud")
            return []
        elif response.status_code != 200:
            print(f"  SonarCloud API error: {response.status_code}")
            return []

        data = response.json()
        findings = []

        for issue in data.get("issues", []):
            findings.append({
                "file": issue.get("component", "").split(":")[-1],
                "line": issue.get("line", 0),
                "type": issue.get("type"),
                "severity": issue.get("severity"),
                "message": issue.get("message"),
                "rule": issue.get("rule"),
                "effort": issue.get("effort"),
            })

        print(f"  SonarCloud: {len(findings)} issues for {project_key}")
        return findings

    except requests.exceptions.Timeout:
        print("  SonarCloud: Request timed out")
        return []
    except Exception as e:
        print(f"  SonarCloud error: {e}")
        return []


def list_sonar_projects():
    """List all projects in your SonarCloud org  useful for debugging."""
    token = os.getenv("SONARCLOUD_TOKEN")
    org = os.getenv("SONARCLOUD_ORG")

    if not token or not org:
        print("  SonarCloud not configured")
        return []

    try:
        response = requests.get(
            f"{BASE_URL}/projects/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"organization": org},
            timeout=10
        )

        if response.status_code != 200:
            print(f"  Could not list projects: {response.status_code}")
            return []

        projects = response.json().get("components", [])
        print(f"  SonarCloud projects in org '{org}':")
        for p in projects:
            print(f"    {p['key']} — {p['name']}")

        return [p["key"] for p in projects]

    except Exception as e:
        print(f"  SonarCloud list error: {e}")
        return []