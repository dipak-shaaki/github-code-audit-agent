# PR Audit Report

## Summary
This PR audit report summarizes the findings from the code review of the feature/vulnerable-modules PR. The report highlights security issues, code quality issues, and provides recommendations for fixes.

## What the Developer Was Trying to Do
The developer was trying to implement API, app, database, and file handling functionality. The code includes features such as user authentication, data fetching, and file operations.

## Security Issues
1. **Insecure Hashing**
	* File: api.py, Line: 14; app.py, Line: 5
	* What is wrong: The code uses the weak MD5 hashing algorithm for security purposes.
	* Why it is dangerous: MD5 is vulnerable to collisions and is not suitable for security purposes.
	* Vulnerable code snippet: `return hashlib.md5(password.encode()).hexdigest()`; `hashed = hashlib.md5(password.encode()).hexdigest()`
	* Fixed code snippet: `import bcrypt; return bcrypt.hashpw(password.encode(), bcrypt.gensalt())`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b324_hashlib.html
2. **SSL Verification Disabled**
	* File: api.py, Line: 18
	* What is wrong: The code disables SSL verification for requests.
	* Why it is dangerous: Disabling SSL verification makes the application vulnerable to man-in-the-middle attacks.
	* Vulnerable code snippet: `response = requests.get(url, verify=False)`
	* Fixed code snippet: `response = requests.get(url, verify=True)`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b501_request_with_no_cert_validation.html
3. **Request without Timeout**
	* File: api.py, Line: 18
	* What is wrong: The code does not set a timeout for requests.
	* Why it is dangerous: Not setting a timeout can lead to indefinite waits and potential denial-of-service attacks.
	* Vulnerable code snippet: `response = requests.get(url, verify=False)`
	* Fixed code snippet: `response = requests.get(url, verify=True, timeout=10)`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b113_request_without_timeout.html
4. **SQL Injection**
	* File: app.py, Line: 11; database.py, Line: 10, 17
	* What is wrong: The code constructs SQL queries using string concatenation.
	* Why it is dangerous: This makes the application vulnerable to SQL injection attacks.
	* Vulnerable code snippet: `cursor.execute("SELECT * FROM users WHERE username = '" + username + "'")`; `cursor.execute("SELECT * FROM users WHERE id = " + user_id)`; `query = "DELETE FROM users WHERE username = '" + username + "'"`
	* Fixed code snippet: `cursor.execute("SELECT * FROM users WHERE username = %s", (username,))`; `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))`; `query = "DELETE FROM users WHERE username = %s"; cursor.execute(query, (username,))`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html
5. **Pickle Insecurity**
	* File: file_handler.py, Line: 9
	* What is wrong: The code uses the insecure pickle module to deserialize data.
	* Why it is dangerous: Pickle can execute arbitrary code, making it a security risk.
	* Vulnerable code snippet: `return pickle.load(f)`
	* Fixed code snippet: `import json; return json.load(f)`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b301-pickle
6. **Shell Injection**
	* File: file_handler.py, Line: 19
	* What is wrong: The code uses the insecure os.system function to execute shell commands.
	* Why it is dangerous: This makes the application vulnerable to shell injection attacks.
	* Vulnerable code snippet: `os.system(cmd)`
	* Fixed code snippet: `import subprocess; subprocess.run(cmd, shell=False)`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b605_start_process_with_a_shell.html

## Code Quality Issues
1. **Unused Variable**
	* File: app.py, Line: 5
	* What is wrong: The variable `hashed` is assigned a value but never used.
	* Fixed code snippet: Remove the unused variable.
	* Documentation link: https://docs.astral.sh/ruff/rules/f841

## Teammate Comments Summary
There are no teammate comments on this PR.

## Fixes with Code Examples
The fixes for the identified issues are provided in the respective sections above.

## Overall Risk Assessment
The overall risk assessment for this PR is **HIGH** due to the presence of multiple high-severity security issues, including SQL injection, insecure hashing, and shell injection vulnerabilities. It is essential to address these issues before merging the PR to ensure the security and integrity of the application.