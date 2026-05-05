import os
from groq import Groq
import json

def generate_review(pr_title, pr_body, diff, all_bandit, all_ruff, metadata=None, dependabot=None):
    prompt = f"""
You are a senior code reviewer. You have tool findings with exact line numbers plus GitHub metadata.

Your job:
1. Explain what the developer was trying to do
2. For each finding state exact line number, what is wrong, why dangerous
3. Show vulnerable code and fixed version side by side
4. Link to documentation for each fix
5. Consider existing review comments from teammates
6. Factor in Dependabot alerts for known vulnerable dependencies
7. Only report issues present in tool findings — do not invent issues

PR TITLE: {pr_title}
PR DESCRIPTION: {pr_body or 'No description provided'}

PR METADATA:
- Labels: {metadata.get('labels', []) if metadata else []}
- Assignees: {metadata.get('assignees', []) if metadata else []}
- Changed files: {metadata.get('changed_files', 0) if metadata else 0}
- Additions: {metadata.get('additions', 0) if metadata else 0}
- Deletions: {metadata.get('deletions', 0) if metadata else 0}
- Branch: {metadata.get('head_branch', '') if metadata else ''} → {metadata.get('base_branch', '') if metadata else ''}

EXISTING REVIEW COMMENTS FROM TEAMMATES:
{json.dumps(metadata.get('comments', []), indent=2) if metadata else '[]'}

DEPENDABOT SECURITY ALERTS:
{json.dumps(dependabot, indent=2) if dependabot else '[]'}

CODE DIFF:
{diff}

BANDIT SECURITY FINDINGS (with line numbers):
{json.dumps(all_bandit, indent=2)}

RUFF CODE QUALITY FINDINGS (with line numbers):
{json.dumps(all_ruff, indent=2)}

Write the report in plain markdown:
# PR Audit Report

## Summary

## What the Developer Was Trying to Do

## Security Issues (from Bandit + Dependabot)
For each issue:
- File and line number
- What is wrong
- Why it is dangerous
- Vulnerable code snippet
- Fixed code snippet
- Documentation link

## Code Quality Issues (from Ruff)
For each issue:
- File and line number
- What is wrong
- Fixed code snippet
- Documentation link

## Teammate Comments Summary

## Overall Risk Assessment
Rate overall PR risk as LOW / MEDIUM / HIGH with one line reason.

IMPORTANT: Do not add issues not present in the tool output above.
"""

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a senior software engineer specializing in code security and quality reviews. Be precise and cite exact line numbers."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def merge_reports(pr_title, mini_reports):
    combined = "\n\n---\n\n".join(mini_reports)

    prompt = f"""
You have multiple partial code review reports for the same PR: {pr_title}
Merge into one clean final report. Remove duplicates. Keep all unique findings.

PARTIAL REPORTS:
{combined}

Write final merged report:
# PR Audit Report
## Summary
## What the Developer Was Trying to Do
## Security Issues
## Code Quality Issues
## Teammate Comments Summary
## Fixes with Code Examples
## Overall Risk Assessment
"""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a senior code reviewer. Merge reports cleanly."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=4096,
    )
    return response.choices[0].message.content