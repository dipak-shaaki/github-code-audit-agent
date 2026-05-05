import os
from github import Github, Auth
from tenacity import retry, stop_after_attempt, wait_exponential
from config.config import SCANNABLE_EXTENSIONS

def get_github_client():
    auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
    return Github(auth=auth)

def get_all_repos():
    g = get_github_client() # authenticates token
    user = g.get_user()     #Access GitHub account
    repos = user.get_repos()  # fetches all repos 

    # only return repos that have open PRs
    active_repos = []
    for repo in repos:
        open_prs = repo.get_pulls(state="open").totalCount
        if open_prs > 0: # skip repos with no open PRs
            print(f"  {repo.full_name} — {open_prs} open PR(s)")
            active_repos.append(repo.full_name)
    
    return active_repos

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_open_prs(repo_name):
    g = get_github_client()
    repo = g.get_repo(repo_name)
    return [pr.number for pr in repo.get_pulls(state="open")]
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
        diff_text += f"\n File: {f.filename} \n"
        diff_text += f.patch if f.patch else ""

        if ext in SCANNABLE:
            try:
                content = repo.get_contents(f.filename, ref=pr.head.sha)
                file_contents[f.filename] = {
                    "code": content.decoded_content.decode(),
                    "ext": ext
                }
            except Exception as e:
                print(f"  Warning: Could not fetch {f.filename}: {e}")

    return pr.title, pr.body, diff_text, file_contents

def get_pr_metadata(repo_name, pr_number):
    g = get_github_client()
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # labels like "bug", "security", "feature"
    labels = [label.name for label in pr.labels]
    
    # existing review comments from other developers
    comments = []
    for comment in pr.get_review_comments():
        comments.append({
            "file": comment.path,
            "line": comment.line,
            "body": comment.body,
            "user": comment.user.login
        })
    
    # who is assigned to review
    assignees = [a.login for a in pr.assignees]
    reviewers = [r.login for r in pr.requested_reviewers]
    
    # PR stats
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

# extract extra PR metadata
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