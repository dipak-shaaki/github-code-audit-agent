import os
from dotenv import load_dotenv
from github_client import (
    get_open_prs,
    get_pr_details,
    get_all_repos,
    get_pr_metadata,
    get_dependabot_alerts,
    get_pr_commits
)
from scanner import analyze_file, chunk_files
from llm_client import generate_review, merge_reports
from reporter import save_report
from sonar_client import get_sonar_issues
from slack_client import send_to_slack

load_dotenv()


def already_scanned(repo_name, pr_number):
    """Check if this PR has already been scanned."""
    scan_log = "logs/scanned.txt"
    key = f"{repo_name}#{pr_number}"
    if os.path.exists(scan_log):
        with open(scan_log, "r") as f:
            return key in f.read()
    return False


def mark_scanned(repo_name, pr_number):
    """Mark PR as scanned to avoid rescanning."""
    os.makedirs("logs", exist_ok=True)
    with open("logs/scanned.txt", "a") as f:
        f.write(f"{repo_name}#{pr_number}\n")


def log_failure(repo_name, pr_number, error):
    """Log failed scans for debugging."""
    os.makedirs("logs", exist_ok=True)
    with open("logs/failures.log", "a") as f:
        f.write(f"{repo_name} PR#{pr_number}: {error}\n")


def scan_pr(repo_name, pr_number):
    """
    Full scan pipeline for a single PR:
    1. Fetch PR details, metadata, commits
    2. Fetch SonarCloud findings
    3. Run Bandit + Ruff on changed files
    4. Generate report chunks
    5. Merge into final report
    6. Save as PDF + markdown
    7. Send to Slack
    """
    print(f"\nScanning {repo_name} PR #{pr_number}...")

    if already_scanned(repo_name, pr_number):
        print(f"  Already scanned — skipping")
        return

    try:
        # step 1 — fetch PR data
        pr_title, pr_body, diff, file_contents = get_pr_details(repo_name, pr_number)
        metadata = get_pr_metadata(repo_name, pr_number)
        dependabot = get_dependabot_alerts(repo_name)

        # step 2 — fetch commit history for context
        commits = get_pr_commits(repo_name, pr_number)
        print(f"  Found {len(commits)} commits in PR")

        # step 3 — fetch SonarCloud findings
        print("  Fetching SonarCloud findings...")
        sonar_findings = get_sonar_issues(pr_number=pr_number)
        print(f"  SonarCloud: {len(sonar_findings)} issues found")

        # step 4 — chunk files and scan
        chunks = chunk_files(file_contents)
        print(f"  {len(file_contents)} files -> {len(chunks)} chunks")

        mini_reports = []

        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}/{len(chunks)}...")
            all_bandit = {}
            all_ruff = {}

            for filename, file_info in chunk.items():
                print(f"    Analyzing {filename}...")
                bandit_findings, ruff_findings = analyze_file(filename, file_info)
                all_bandit[filename] = bandit_findings
                all_ruff[filename] = ruff_findings

            mini_report = generate_review(
                pr_title, pr_body, diff,
                all_bandit, all_ruff,
                metadata, dependabot,
                sonar_findings,
                commits
            )
            mini_reports.append(mini_report)

        # step 5 — merge chunks
        final_report = merge_reports(pr_title, mini_reports)

        # step 6 — extract risk level BEFORE saving
        risk_level = "UNKNOWN"
        if "HIGH" in final_report.upper():
            risk_level = "HIGH"
        elif "MEDIUM" in final_report.upper():
            risk_level = "MEDIUM"
        elif "LOW" in final_report.upper():
            risk_level = "LOW"

        # step 7 — save PDF + markdown
        report_path = save_report(repo_name, pr_number, final_report, risk_level)

        # step 8 — send to Slack
        send_to_slack(repo_name, pr_number, report_path, risk_level)

        # step 9 — mark as scanned
        mark_scanned(repo_name, pr_number)

    except Exception as e:
        print(f"  Failed: {e}")
        import traceback
        traceback.print_exc()
        log_failure(repo_name, pr_number, str(e))


def scan_all():
    """
    Weekly scan entry point.
    Discovers all repos with open PRs automatically.
    Scheduled via cron: 0 9 * * 1 (every Monday 9am)
    """
    REPOS = get_all_repos()
    print(f"Found {len(REPOS)} repos with open PRs")

    for repo in REPOS:
        print(f"\nRepo: {repo}")
        try:
            prs = get_open_prs(repo)
            if not prs:
                print("  No open PRs.")
                continue
            print(f"  Open PRs: {prs}")
            for pr_num in prs:
                scan_pr(repo, pr_num)
        except Exception as e:
            print(f"  Could not process repo {repo}: {e}")


# cron: 0 9 * * 1 — runs every Monday 9am
if __name__ == "__main__":
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("GITHUB_REPO")

    if pr_number and repo:
        scan_pr(repo, int(pr_number))
    else:
        scan_all()