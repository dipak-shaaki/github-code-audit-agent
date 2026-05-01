import os
from groq import Groq
import json

def generate_review(pr_title, pr_body, diff, all_bandit, all_ruff):
    prompt = f"""
You are a senior code reviewer. You have tool findings with exact line numbers.

Your job:
1. Explain what the developer was trying to do
2. For each finding state the exact line number, what is wrong, why it is dangerous
3. Show the vulnerable code and the fixed version side by side
4. Link to documentation for each fix
5. Only report issues present in the tool findings below — do not invent issues

PR TITLE: {pr_title}
PR DESCRIPTION: {pr_body or 'No description provided'}

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

## Security Issues
For each issue:
- File and line number
- What is wrong
- Why it is dangerous
- Vulnerable code snippet
- Fixed code snippet
- Documentation link

## Code Quality Issues
For each issue:
- File and line number
- What is wrong
- Fixed code snippet
- Documentation link

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