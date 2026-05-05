import os
import re
from github import Github, Auth
from tenacity import retry, stop_after_attempt, wait_exponential
from config.config import SCANNABLE_EXTENSIONS


def get_github_client():
    auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
    return Github(auth=auth)


def get_all_repos():
    g = get_github_client()
    user = g.get_user()
    repos = user.get_repos()

    active_repos = []
    for repo in repos:
        open_prs = repo.get_pulls(state="open").totalCount
        if open_prs > 0:
            print(f"  {repo.full_name} — {open_prs} open PR(s)")
            active_repos.append(repo.full_name)

    return active_repos


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_open_prs(repo_name):
    g = get_github_client()
    repo = g.get_repo(repo_name)
    return [pr.number for pr in repo.get_pulls(state="open")]


def extract_added_lines(patch):
    """Extract only added lines from diff patch with their line numbers."""
    if not patch:
        return []

    added_lines = []
    line_number = 0

    for line in patch.split("\n"):
        if line.startswith("@@"):
            # parse starting line number from @@ -x,y +start,count @@
            match = re.search(r"\+(\d+)", line)
            if match:
                line_number = int(match.group(1)) - 1
        elif line.startswith("+") and not line.startswith("+++"):
            line_number += 1
            added_lines.append({
                "line_number": line_number,
                "code": line[1:]  # strip the + prefix
            })
        elif not line.startswith("-"):
            line_number += 1

    return added_lines


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_pr_details(repo_name, pr_number):
    g = get_github_client()
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    SCANNABLE = set(SCANNABLE_EXTENSIONS.keys())
    diff_text = ""
    file_contents = {}

    for f in pr.get_files():
        ext = os.path.splitext(f.filename)[1].lower()
        diff_text += f"\nFile: {f.filename}\n"
        diff_text += f.patch if f.patch else ""

        if ext in SCANNABLE:
            # only extract added lines — not full file
            added_lines = extract_added_lines(f.patch)
            if added_lines:
                changed_code = "\n".join([l["code"] for l in added_lines])
                file_contents[f.filename] = {
                    "code": changed_code,        # only changed lines
                    "ext": ext,
                    "added_lines": added_lines   # line numbers preserved
                }

    return pr.title, pr.body, diff_text, file_contents


def get_pr_metadata(repo_name, pr_number):
    g = get_github_client()
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    labels = [label.name for label in pr.labels]

    comments = []
    for comment in pr.get_review_comments():
        comments.append({
            "file": comment.path,
            "line": comment.line,
            "body": comment.body,
            "user": comment.user.login
        })

    assignees = [a.login for a in pr.assignees]
    reviewers = [r.login for r in pr.requested_reviewers]

    metadata = {
        "labels": labels,
        "assignees": assignees,
        "reviewers": reviewers,
        "comments": comments,
        "changed_files": pr.changed_files,
        "additions": pr.additions,
        "deletions": pr.deletions,
        "base_branch": pr.base.ref,
        "head_branch": pr.head.ref,
    }

    return metadata


def get_dependabot_alerts(repo_name):
    """Fetch GitHub Dependabot security alerts."""
    g = get_github_client()
    repo = g.get_repo(repo_name)

    alerts = []
    try:
        for alert in repo.get_dependabot_alerts():
            alerts.append({
                "package": alert.dependency.package.name,
                "severity": alert.security_advisory.severity,
                "summary": alert.security_advisory.summary,
                "vulnerable_version": alert.dependency.manifest_path,
            })
    except Exception as e:
        print(f"  Could not fetch Dependabot alerts: {e}")

    return alerts