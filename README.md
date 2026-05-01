# GitHub Security & Code Audit Agent

An automated agent that scans GitHub repositories daily, analyzes pull requests for security vulnerabilities and code quality issues, and generates detailed markdown reports.

## What It Does

- Auto-discovers all GitHub repos with open PRs
- Runs Bandit (security) and Ruff (code quality) on changed Python files
- Extracts exact line numbers, severity, and issue descriptions
- Feeds structured findings to an LLM to generate human-readable reports
- Reports include vulnerable code, fixed code, documentation links, and overall risk rating
- Runs daily automatically via cron

## Project Structure
app/
├── agent.py          # Entry point — orchestrates everything
├── github_client.py  # GitHub API — repo and PR discovery
├── scanner.py        # Bandit + Ruff analysis
├── llm_client.py     # Groq LLM report generation
├── reporter.py       # Saves reports to file
└── config.py         # Supported file extensions
reports/              # Generated audit reports saved here
logs/                 # Failure logs and cron output

## Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- GitHub Personal Access Token (repo scope)
- Groq API Key (free at console.groq.com)

## Setup

**1. Clone the repo:**
```bash
git clone https://github.com/yourname/github-code-audit-agent
cd github-code-audit-agent
```

**2. Install uv:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**3. Create virtual environment and install dependencies:**
```bash
uv venv
source .venv/bin/activate
uv add anthropic pygithub bandit ruff python-dotenv tenacity groq
```

**4. Create `.env` file in the root:**
## How It Works
cron triggers agent.py daily
↓
GitHub API discovers repos with open PRs
↓
Fetches changed Python files + diff per PR
↓
Bandit scans for security issues
Ruff scans for code quality issues
↓
Structured findings sent to Groq LLM
↓
LLM generates report with line numbers,
fixes, documentation links, risk rating
↓
Report saved to reports/reponame_pr_number.md

## Report Structure

Each generated report contains:
- **Summary** — overview of findings
- **What the Developer Was Trying to Do** — intent from PR title and diff
- **Security Issues** — from Bandit with line numbers, vulnerable code, fixed code, docs
- **Code Quality Issues** — from Ruff with line numbers and fixes
- **Overall Risk Assessment** — LOW / MEDIUM / HIGH with reasoning

## Hallucination Guard

The LLM only explains and fixes issues found by Bandit and Ruff. It never invents issues on its own. All findings are grounded in tool output before being passed to the LLM.

## In Progress

- Chunking for large PRs (token limit handling)
- Full repo scan mode (entire codebase, not just PRs)

## Dependencies

| Package | Purpose |
|---|---|
| pygithub | GitHub API client |
| bandit | Python security scanner |
| ruff | Python code quality scanner |
| groq | LLM API client |
| tenacity | Retry logic with exponential backoff |
| python-dotenv | Environment variable management |