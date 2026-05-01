import os
from dotenv import load_dotenv
from github_client import get_open_prs, get_pr_details, get_all_repos
from scanner import analyze_file
from llm_client import generate_review
from reporter import save_report

load_dotenv()

def scan_pr(repo_name, pr_number):
    print(f"\nScanning {repo_name} PR #{pr_number}...")
    try:
        pr_title, pr_body, diff, file_contents = get_pr_details(repo_name, pr_number)

        all_bandit = {}
        all_ruff = {}

        for filename, file_info in file_contents.items():
         print(f"  Analyzing {filename}...")
        bandit_findings, ruff_findings = analyze_file(filename, file_info)
        all_bandit[filename] = bandit_findings
        all_ruff[filename] = ruff_findings


        print("  Sending to Groq...")
        report = generate_review(pr_title, pr_body, diff, all_bandit, all_ruff)
        save_report(repo_name, pr_number, report)

    except Exception as e:
        import traceback
        print(f"  ERROR: {e}")
        traceback.print_exc()
        log_failure(repo_name, pr_number, str(e))

def log_failure(repo_name, pr_number, error):
    os.makedirs("logs", exist_ok=True)
    with open("logs/failures.log", "a") as f:
        f.write(f"{repo_name} PR#{pr_number}: {error}\n")


def scan_all():
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





if __name__ == "__main__":
    scan_all()