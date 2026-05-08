import os
from dotenv import load_dotenv
from github_client import (
    get_open_prs,
    get_pr_details,
    get_all_repos,
    get_pr_metadata,
    get_dependabot_alerts,
    get_pr_commits,
    get_all_scannable_files
)
from subagents.security_agent import analyze_security
from subagents.quality_agent import analyze_quality
from subagents.actions_agent import analyze_github_actions
from subagents.report_agent import generate_full_report
from reporter import save_report
from sonar_client import get_sonar_issues
from slack_client import send_to_slack

load_dotenv()


def already_scanned(repo_name, pr_number):
    scan_log = "logs/scanned.txt"
    key = f"{repo_name}#{pr_number}"
    if os.path.exists(scan_log):
        with open(scan_log, "r") as f:
            return key in f.read()
    return False


def mark_scanned(repo_name, pr_number):
    os.makedirs("logs", exist_ok=True)
    with open("logs/scanned.txt", "a") as f:
        f.write(f"{repo_name}#{pr_number}\n")


def log_failure(repo_name, identifier, error):
    os.makedirs("logs", exist_ok=True)
    with open("logs/failures.log", "a") as f:
        f.write(f"{repo_name} {identifier}: {error}\n")


def scan_repo(repo_name):
    """
    Main Agent orchestrates full repo scan.
    
    Flow:
    1. Fetch ALL scannable files from entire repo
    2. Delegate to security subagent
    3. Delegate to quality subagent  
    4. Delegate to actions subagent
    5. Fetch all open PRs and their changed files
    6. Run subagents on each PR's changed files
    7. Delegate to report subagent for final unified report
    8. Save PDF + send to Slack
    """
    print(f"\nFull repo scan: {repo_name}")

    try:
        # step 1 — fetch all files in repo
        print("  Fetching all files...")
        all_files = get_all_scannable_files(repo_name)
        print(f"  Found {len(all_files)} scannable files")

        # step 2 — delegate to security subagent
        print("  Security subagent running...")
        repo_security = analyze_security(all_files)
        print(f"  Security: {len(repo_security)} files with issues")

        # step 3 — delegate to quality subagent
        print("  Quality subagent running...")
        repo_quality = analyze_quality(all_files)
        print(f"  Quality: {len(repo_quality)} files with issues")

        # step 4 — delegate to actions subagent
        print("  Actions subagent running...")
        repo_actions = analyze_github_actions(all_files)
        print(f"  Actions: {len(repo_actions)} workflow files with issues")

        # step 5 — fetch SonarCloud full repo findings
        print("  Fetching SonarCloud findings...")
        sonar_findings = get_sonar_issues()  # no pr_number = full repo
        print(f"  SonarCloud: {len(sonar_findings)} issues")

        # step 6 — scan each open PR
        pr_findings = {}
        commits_by_pr = {}

        open_prs = get_open_prs(repo_name)
        print(f"  Found {len(open_prs)} open PRs: {open_prs}")

        for pr_num in open_prs:
            print(f"  Scanning PR #{pr_num}...")

            if already_scanned(repo_name, pr_num):
                print(f" PR #{pr_num} Already scanned  skipping")
                continue

            try:
                pr_title, pr_body, diff, pr_files = get_pr_details(repo_name, pr_num)
                commits = get_pr_commits(repo_name, pr_num)
                commits_by_pr[pr_num] = commits

                # run subagents on PR changed files only
                pr_security = analyze_security(pr_files)
                pr_quality = analyze_quality(pr_files)
                pr_actions = analyze_github_actions(pr_files)

                pr_findings[pr_num] = {
                    "title": pr_title,
                    "body": pr_body,
                    "diff": diff,
                    "security": pr_security,
                    "quality": pr_quality,
                    "actions": pr_actions
                }

                mark_scanned(repo_name, pr_num)

            except Exception as e:
                print(f"    PR #{pr_num} failed: {e}")
                log_failure(repo_name, f"PR#{pr_num}", str(e))

        # step 7 — report subagent generates final unified report
        print("  Report subagent generating final report...")
        final_report = generate_full_report(
            repo_name,
            repo_security,
            repo_quality,
            repo_actions,
            sonar_findings,
            pr_findings,
            commits_by_pr
        )

        # step 8 — extract risk level
        risk_level = "UNKNOWN"
        if "HIGH" in final_report.upper():
            risk_level = "HIGH"
        elif "MEDIUM" in final_report.upper():
            risk_level = "MEDIUM"
        elif "LOW" in final_report.upper():
            risk_level = "LOW"

        # step 9 — save PDF + markdown
        report_path = save_report(
            repo_name,
            "full_scan",
            final_report,
            risk_level
        )

        # step 10 — send to Slack
        send_to_slack(repo_name, "full_scan", report_path, risk_level)

    except Exception as e:
        print(f"  Repo scan failed: {e}")
        import traceback
        traceback.print_exc()
        log_failure(repo_name, "full_scan", str(e))


def scan_all():
    """
    Weekly entry point.
    Gets all repos and runs full scan on each.
    Cron: 0 9 * * 1 — every Monday 9am
    """
    from github_client import get_all_repos_full
    REPOS = get_all_repos_full()
    print(f"Found {len(REPOS)} repos to scan")

    for repo in REPOS:
        scan_repo(repo)


# cron: 0 9 * * 1 — every Monday 9am
if __name__ == "__main__":
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("GITHUB_REPO")

    if pr_number and repo:
        # GitHub Actions mode — scan specific PR inside full repo scan
        scan_repo(repo)
    else:
        # cron mode — scan all repos
        scan_all()