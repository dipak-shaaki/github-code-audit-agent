# PR Audit Report

## Summary
This PR audit report is based on the provided code diff and tool findings. The PR title is "Demo/security issues" and the description is empty. The code changes include modifications to the GitHub workflow file, additions to the app.py file, and new config and vulnerable script files. The report will focus on security and code quality issues identified by Bandit, Ruff, and SonarCloud.

## What the Developer Was Trying to Do
The developer was trying to modify the GitHub workflow file to change the security scan and add new functionality to the app.py file, including various functions that seem to be intentionally vulnerable. The purpose of these changes is unclear, but they appear to be related to demonstrating security issues.

## Security Issues (Bandit + Dependabot + SonarCloud)
### Hardcoded Credentials in app.py
```python
# === HARD CODED SECRETS (Secret Scanning will catch these) ===
SECRET_KEY = "supersecret_hardcoded_key_12345"  # ← ISSUE HERE
DB_PASSWORD = "P@ssw0rd2026!"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
API_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz123456"
```
The issue here is that sensitive credentials are hardcoded in the code. This is a significant security risk as it can lead to unauthorized access to sensitive data.
Corrected version:
```python
# === HARD CODED SECRETS (Secret Scanning will catch these) ===
SECRET_KEY = os.environ.get('SECRET_KEY')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
API_TOKEN = os.environ.get('API_TOKEN')
```
See [Python documentation on environment variables](https://docs.python.org/3/library/os.html#os.environ) for more information.

### Hardcoded PostgreSQL Password in config.py
```python
DATABASE_URL = "postgresql://user:SuperSecretPass123@db.example.com/prod"  # ← ISSUE HERE
```
The issue here is that a sensitive PostgreSQL password is hardcoded in the code. This is a significant security risk as it can lead to unauthorized access to the database.
Corrected version:
```python
DATABASE_URL = os.environ.get('DATABASE_URL')
```
See [Python documentation on environment variables](https://docs.python.org/3/library/os.html#os.environ) for more information.

### Hardcoded Secret in config.py
```python
SECRET = "dev-secret-123456789"  # ← ISSUE HERE
```
The issue here is that a sensitive secret is hardcoded in the code. This is a security risk as it can lead to unauthorized access to sensitive data.
Corrected version:
```python
SECRET = os.environ.get('SECRET')
```
See [Python documentation on environment variables](https://docs.python.org/3/library/os.html#os.environ) for more information.

## Code Quality Issues (Ruff + SonarCloud)
### Unexpected Indentation in app.py
```python
os.system("ls " + user_input)          # Dangerous  # ← ISSUE HERE
```
The issue here is that there is unexpected indentation in the code. This can lead to code readability issues and potential bugs.
Corrected version:
```python
os.system("ls " + user_input)  # Dangerous
```
See [Ruff documentation on invalid syntax](https://docs.astral.sh/ruff/rules/invalid-syntax) for more information.

### Unused Import in vulnerable_script.py
```python
from app import run_command, load_pickle_unsafe  # ← ISSUE HERE
```
The issue here is that the `load_pickle_unsafe` function is imported but not used. This can lead to code clutter and potential bugs.
Corrected version:
```python
from app import run_command
```
See [Ruff documentation on unused imports](https://docs.astral.sh/ruff/rules/f401) for more information.

## Teammate Comments Summary
There are no teammate comments on this PR.

## Overall Risk Assessment
- **Risk Level**: HIGH
- Reason: The PR introduces several significant security risks, including hardcoded credentials and secrets, which can lead to unauthorized access to sensitive data.