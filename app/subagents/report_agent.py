import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI


def generate_full_report(
    repo_name,
    repo_security,
    repo_quality,
    repo_actions,
    sonar_findings,
    pr_findings,
    commits_by_pr,
    semgrep_findings=None,
):
    """
    Report Subagent — one job: write the final unified report.
    
    How it works:
    1. Receives findings from all three scanner subagents
    2. Receives PR-specific findings
    3. Builds a structured prompt with two clear sections:
       Section 1 — Repository Issues (full codebase)
       Section 2 — Pull Request Analysis (per PR)
    4. Sends to OpenAI LLM
    5. Returns formatted markdown report
    
    Why LLM here and not in scanner subagents?
    Scanner subagents return raw structured data.
    This agent's job is to translate that data into
    human-readable explanations with fixes and docs.
    LLM only explains — never discovers issues itself.
    That's our hallucination guard.
    
    pr_findings structure:
    {
        4: {
            "title": "Add security utilities",
            "security": {...},
            "quality": {...},
            "actions": {...}
        },
        3: {
            "title": "Add reports endpoint",
            "security": {...},
            "quality": {...},
            "actions": {...}
        }
    }
    """

    # build PR analysis section
    pr_section = ""
    for pr_num, pr_data in pr_findings.items():
        pr_section += f"\nPR #{pr_num} — {pr_data.get('title', 'No title')}\n"
        pr_section += f"Commits: {json.dumps(commits_by_pr.get(pr_num, []), indent=2)}\n"
        pr_section += f"Security findings: {json.dumps(pr_data.get('security', {}), indent=2)}\n"
        pr_section += f"Quality findings: {json.dumps(pr_data.get('quality', {}), indent=2)}\n"
        pr_section += f"Actions findings: {json.dumps(pr_data.get('actions', {}), indent=2)}\n"

    prompt = f"""
You are a senior code reviewer writing a comprehensive repository audit report.
You have findings from three specialist teams plus PR-specific analysis.

IMPORTANT: Only report issues present in the findings below. Do not invent issues.
For every issue show the full function with the problematic line marked as # <- ISSUE HERE.

REPOSITORY: {repo_name}

===== SECTION 1: FULL REPOSITORY FINDINGS =====

SECURITY FINDINGS (Bandit + Semgrep across entire repo):
{json.dumps(repo_security, indent=2) if repo_security else 'No security issues found.'}

CODE QUALITY FINDINGS (Ruff across entire repo):
{json.dumps(repo_quality, indent=2) if repo_quality else 'No quality issues found.'}

GITHUB ACTIONS FINDINGS (Semgrep yaml rules):
{json.dumps(repo_actions, indent=2) if repo_actions else 'No GitHub Actions issues found.'}

SONARCLOUD FINDINGS (full repo):
{json.dumps(sonar_findings, indent=2) if sonar_findings else 'No SonarCloud findings.'}

===== SECTION 2: PULL REQUEST ANALYSIS =====

{pr_section if pr_section else 'No open pull requests.'}

Write the final report in this exact markdown structure:

# Repository Audit Report — {repo_name}

## Repository Overview
- Total security issues found: (count)
- Total quality issues found: (count)
- GitHub Actions vulnerabilities: (count)
- Open PRs analyzed: (count)

## Repository Issues

### Security Issues
For each issue:
- File + Function name + Line number
- Full function code with # <- ISSUE HERE on the bad line
- Why it is dangerous
- Fixed version of the full function
- Documentation link

### Code Quality Issues
For each issue:
- File + Function name + Line number
- Full function code with # <- ISSUE HERE
- What is wrong
- Fixed version

### GitHub Actions Vulnerabilities
For each issue:
- Workflow file + Line number
- The vulnerable code
- Why it is dangerous
- Fixed version

## Pull Request Analysis

### PR #[number] — [title] — [risk level]
For each PR:
- What the developer was trying to do
- Issues found in changed files only
- Fixes specific to this PR

## Overall Risk Assessment
- Risk Level: LOW / MEDIUM / HIGH
- Reason: one sentence summary

IMPORTANT: Do not add issues not present in the findings above.
"""

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict senior engineer writing audit reports. Never hallucinate issues. Always show full function code with issues marked."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_completion_tokens=6000,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"  Report agent error: {e}")
        return f"Failed to generate report: {str(e)}"