# PR Audit Report

## Summary
This PR audit report summarizes the findings from the code review of the feature/vulnerable-modules PR. The report highlights security issues, code quality issues, and provides recommendations for fixes.

## What the Developer Was Trying to Do
The developer was trying to implement API endpoints, database interactions, and file handling functionality. However, the implementation contains several security vulnerabilities and code quality issues.

## Security Issues
1. **File: api.py, Line: 14**
	* What is wrong: Use of weak MD5 hash for security.
	* Why it is dangerous: MD5 is a weak hashing algorithm that can be easily broken, allowing attackers to obtain the original password.
	* Vulnerable code snippet: `return hashlib.md5(password.encode()).hexdigest()`
	* Fixed code snippet: `import bcrypt; return bcrypt.hashpw(password.encode(), bcrypt.gensalt())`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b324_hashlib.html
2. **File: api.py, Line: 18**
	* What is wrong: Call to requests with verify=False disabling SSL certificate checks and without timeout.
	* Why it is dangerous: Disabling SSL certificate checks makes the application vulnerable to man-in-the-middle attacks, and not setting a timeout can cause the application to hang indefinitely, leading to denial-of-service attacks.
	* Vulnerable code snippet: `response = requests.get(url, verify=False)`
	* Fixed code snippet: `response = requests.get(url, verify=True, timeout=10)`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b501_request_with_no_cert_validation.html, https://bandit.readthedocs.io/en/1.9.4/plugins/b113_request_without_timeout.html
3. **File: app.py, Line: 6**
	* What is wrong: Use of weak MD5 hash for security.
	* Why it is dangerous: MD5 is a weak hashing algorithm that can be easily broken, allowing attackers to obtain the original password.
	* Vulnerable code snippet: `hashed = hashlib.md5(password.encode()).hexdigest()`
	* Fixed code snippet: `import bcrypt; hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b324_hashlib.html
4. **File: app.py, Line: 12**
	* What is wrong: Possible SQL injection vector through string-based query construction.
	* Why it is dangerous: SQL injection attacks can allow attackers to access and modify sensitive data.
	* Vulnerable code snippet: `cursor.execute("SELECT * FROM users WHERE username = '" + username + "'")`
	* Fixed code snippet: `cursor.execute("SELECT * FROM users WHERE username = %s", (username,))`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html
5. **File: database.py, Line: 10**
	* What is wrong: Possible SQL injection vector through string-based query construction.
	* Why it is dangerous: SQL injection attacks can allow attackers to access and modify sensitive data.
	* Vulnerable code snippet: `cursor.execute("SELECT * FROM users WHERE id = " + user_id)`
	* Fixed code snippet: `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html
6. **File: database.py, Line: 17**
	* What is wrong: Possible SQL injection vector through string-based query construction.
	* Why it is dangerous: SQL injection attacks can allow attackers to access and modify sensitive data.
	* Vulnerable code snippet: `query = "DELETE FROM users WHERE username = '" + username + "'"`
	* Fixed code snippet: `query = "DELETE FROM users WHERE username = %s"; cursor.execute(query, (username,))`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html
7. **File: file_handler.py, Line: 9**
	* What is wrong: Pickle and modules that wrap it can be unsafe when used to deserialize untrusted data.
	* Why it is dangerous: Deserializing untrusted data can lead to arbitrary code execution.
	* Vulnerable code snippet: `return pickle.load(f)`
	* Fixed code snippet: `import json; return json.load(f)`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/blacklists/blacklist_calls.html#b301-pickle
8. **File: file_handler.py, Line: 19**
	* What is wrong: Starting a process with a shell, possible injection detected.
	* Why it is dangerous: Starting a process with a shell can lead to shell injection attacks.
	* Vulnerable code snippet: `os.system(cmd)`
	* Fixed code snippet: `import subprocess; subprocess.run(cmd, shell=False)`
	* Documentation link: https://bandit.readthedocs.io/en/1.9.4/plugins/b605_start_process_with_a_shell.html

## Code Quality Issues
1. **File: app.py, Line: 6**
	* What is wrong: Local variable `hashed` is assigned to but never used.
	* Fixed code snippet: Remove the `hashed` variable or use it in the code.
	* Documentation link: https://docs.astral.sh/ruff/rules/f841

## Teammate Comments Summary
There are no teammate comments on this PR.

## Fixes with Code Examples
The fixes for the identified issues are provided in the respective sections above.

## Overall Risk Assessment
The overall PR risk is **HIGH** due to the presence of multiple high-severity security vulnerabilities, including SQL injection, weak hashing, and shell injection. It is recommended to address these issues before merging the PR.