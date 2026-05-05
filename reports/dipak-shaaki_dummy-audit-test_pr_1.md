# PR Audit Report

## Summary
This PR audit report reviews the changes made in the `addauth` PR, focusing on security and code quality issues identified by Bandit and Ruff.

## What the Developer Was Trying to Do
The developer was trying to add authentication functionality to the application, including user login and password reset features.

## Security Issues
### Issue 1: Weak Hashing
- File and line number: `app.py`, line 6
- What is wrong: The code uses MD5 hashing for security purposes, which is considered weak.
- Why it is dangerous: MD5 is vulnerable to collisions and can be easily broken by attackers, compromising password security.
- Vulnerable code snippet:
  ```python
hashed = hashlib.md5(password.encode()).hexdigest()
```
- Fixed code snippet:
  ```python
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```
- Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b324_hashlib.html

### Issue 2: SQL Injection
- File and line number: `app.py`, line 12
- What is wrong: The code constructs a SQL query using string concatenation, making it vulnerable to SQL injection attacks.
- Why it is dangerous: An attacker could inject malicious SQL code, potentially leading to data breaches or system compromise.
- Vulnerable code snippet:
  ```python
cursor.execute("SELECT * FROM users WHERE username = '" + username + "'")
```
- Fixed code snippet:
  ```python
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```
- Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html

## Code Quality Issues
### Issue 1: Unused Variable
- File and line number: `app.py`, line 6
- What is wrong: The `hashed` variable is assigned a value but never used.
- Fixed code snippet:
  ```python
# Remove the unused variable or use it as needed
# hashed = hashlib.md5(password.encode()).hexdigest()
```
- Documentation link: https://docs.astral.sh/ruff/rules/f841

## Teammate Comments Summary
There are no existing review comments from teammates.

## Fixes with Code Examples
To address the identified issues, the following fixes are recommended:
- Replace MD5 hashing with bcrypt hashing for secure password storage.
- Use parameterized SQL queries to prevent SQL injection attacks.
- Remove or utilize the unused `hashed` variable.

## Overall Risk Assessment
The overall PR risk is rated as **HIGH** due to the presence of significant security vulnerabilities, including weak hashing and SQL injection, which could compromise the application's security and user data. It is essential to address these issues before merging the PR to ensure the security and integrity of the application.