import os
import json
from groq import Groq
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
) -> str:
    
    prompt = f"""You are an expert senior software engineer specializing in security and code quality reviews.

Your task is to produce a professional, actionable PR review based **only** on the data provided below.
Do not invent or hallucinate any issues that are not present in the tool findings.

PR TITLE: {pr_title}
PR DESCRIPTION: {pr_body or 'No description provided.'}

PR METADATA:
- Labels: {metadata.get('labels', []) if metadata else []}
- Assignees: {metadata.get('assignees', []) if metadata else []}
- Changed files: {metadata.get('changed_files', 0) if metadata else 0}
- Additions: {metadata.get('additions', 0) if metadata else 0}
- Deletions: {metadata.get('deletions', 0) if metadata else 0}
- Branch: {metadata.get('head_branch', 'unknown')} → {metadata.get('base_branch', 'unknown')}

EXISTING REVIEW COMMENTS FROM TEAMMATES:
{json.dumps(metadata.get('comments', []) if metadata else [], indent=2)}

DEPENDABOT SECURITY ALERTS:
{json.dumps(dependabot, indent=2) if dependabot else 'No Dependabot alerts.'}

CODE DIFF:
{diff}

BANDIT SECURITY FINDINGS (by file):
{json.dumps(all_bandit, indent=2) if all_bandit else 'No Bandit findings.'}

RUFF CODE QUALITY FINDINGS (by file):
{json.dumps(all_ruff, indent=2) if all_ruff else 'No Ruff findings.'}

SONARCLOUD FINDINGS:
{json.dumps(sonar_findings, indent=2) if sonar_findings else 'No SonarCloud findings.'}

Instructions:
1. First, briefly explain what the developer was trying to achieve based on the PR title, description and diff.
2. Only report real findings from Bandit, Ruff, or SonarCloud.
3. For every issue:
   - Show the full function/method containing the issue.
   - Mark the exact problematic line with: `# ← ISSUE HERE`
   - Explain why it's problematic and its risk.
   - Provide a corrected version of the full function.
   - Add a link to official documentation when possible.
4. Group issues clearly under Security and Code Quality sections.

Output in clean Markdown with this exact structure:

# PR Audit Report

## Summary
(One paragraph overview)

## What the Developer Was Trying to Do

## Security Issues (Bandit + Dependabot + SonarCloud)
(One subsection per issue)

## Code Quality Issues (Ruff + SonarCloud)
(One subsection per issue)

## Teammate Comments Summary

## Overall Risk Assessment
- **Risk Level**: LOW / MEDIUM / HIGH
- Reason: (one sentence)

Be concise, professional, and actionable."""

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a strict, highly experienced senior engineer doing security and code reviews. Never hallucinate issues."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,      
            max_tokens=6000,      
            top_p=0.9,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f" Error calling Groq API: {e}")
        return f"Failed to generate AI review: {str(e)}"


def merge_reports(pr_title: str, mini_reports: List[str]) -> str:
    if len(mini_reports) == 1:
        return mini_reports[0]

    combined = "\n\n---\n\n".join(mini_reports)

    prompt = f"""You are merging multiple partial review reports for the same PR: **{pr_title}**

PARTIAL REPORTS:
{combined}

Create one clean, final, well-organized report.
- Remove duplicate findings
- Keep all unique valuable insights
- Maintain high quality and clarity

Use this exact structure:

# PR Audit Report

## Summary
## What the Developer Was Trying to Do
## Security Issues
## Code Quality Issues
## Teammate Comments Summary
## Overall Risk Assessment"""

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert at merging code review reports cleanly and removing duplicates."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=6000,
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f" Error merging reports: {e}")
        return "\n\n".join(mini_reports)  # Fallback: just combine them