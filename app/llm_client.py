import os
import json
from openai import OpenAI
from typing import Dict, Any, List, Optional


def generate_review(
    pr_title: str,
    pr_body: Optional[str],
    diff: str,
    all_bandit: Dict[str, List[Dict]],
    all_ruff: Dict[str, List[Dict]],
    metadata: Optional[Dict] = None,
    dependabot: Optional[List] = None,
    sonar_findings: Optional[List] = None,
    commits: Optional[List] = None
) -> str:

    prompt = f"""You are an expert senior software engineer specializing in security and code quality reviews.

Your task is to produce a professional, actionable PR review based only on the data provided below.
Do not invent or hallucinate any issues that are not present in the tool findings.

PR TITLE: {pr_title}
PR DESCRIPTION: {pr_body or 'No description provided.'}

PR METADATA:
- Labels: {metadata.get('labels', []) if metadata else []}
- Assignees: {metadata.get('assignees', []) if metadata else []}
- Changed files: {metadata.get('changed_files', 0) if metadata else 0}
- Additions: {metadata.get('additions', 0) if metadata else 0}
- Deletions: {metadata.get('deletions', 0) if metadata else 0}
- Branch: {metadata.get('head_branch', 'unknown')} -> {metadata.get('base_branch', 'unknown')}

EXISTING REVIEW COMMENTS FROM TEAMMATES:
{json.dumps(metadata.get('comments', []) if metadata else [], indent=2)}

DEPENDABOT SECURITY ALERTS:
{json.dumps(dependabot, indent=2) if dependabot else 'No Dependabot alerts.'}

CODE DIFF:
{diff}

BANDIT SECURITY FINDINGS:
{json.dumps(all_bandit, indent=2) if all_bandit else 'No Bandit findings.'}

RUFF CODE QUALITY FINDINGS:
{json.dumps(all_ruff, indent=2) if all_ruff else 'No Ruff findings.'}

SONARCLOUD FINDINGS:
{json.dumps(sonar_findings, indent=2) if sonar_findings else 'No SonarCloud findings.'}

COMMIT HISTORY:
{json.dumps(commits, indent=2) if commits else 'No commits found.'}

Instructions:
1. Briefly explain what the developer was trying to achieve.
2. Only report real findings from Bandit, Ruff, or SonarCloud.
3. For every issue:
   - Show the full function containing the issue
   - Mark the exact problematic line with: # <- ISSUE HERE
   - Explain why it is problematic and its risk
   - Provide a corrected version of the full function
   - Add a link to official documentation
4. Group issues under Security and Code Quality sections.

Output in clean Markdown:

# PR Audit Report

## Summary

## What the Developer Was Trying to Do

## Security Issues (Bandit + Dependabot + SonarCloud)

## Code Quality Issues (Ruff + SonarCloud)

## Teammate Comments Summary

## Overall Risk Assessment
- Risk Level: LOW / MEDIUM / HIGH
- Reason: one sentence
"""

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": "You are a strict senior engineer doing security and code reviews. Never hallucinate issues."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_completion_tokens=4000,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return f"Failed to generate AI review: {str(e)}"


def merge_reports(pr_title: str, mini_reports: List[str]) -> str:
    if len(mini_reports) == 1:
        return mini_reports[0]

    combined = "\n\n---\n\n".join(mini_reports)

    prompt = f"""Merge these partial review reports for PR: {pr_title}

PARTIAL REPORTS:
{combined}

Create one clean final report removing duplicates:

# PR Audit Report
## Summary
## What the Developer Was Trying to Do
## Security Issues
## Code Quality Issues
## Teammate Comments Summary
## Overall Risk Assessment
"""

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "system", "content": "You are an expert at merging code review reports cleanly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_completion_tokens=4000,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error merging reports: {e}")
        return "\n\n".join(mini_reports)