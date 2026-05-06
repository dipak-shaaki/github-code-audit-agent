import os

def save_report(repo_name, pr_number, content):
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/{repo_name.replace('/', '_')}_pr_{pr_number}.md"
    with open(filename, "w") as f:
        f.write(content)
    print(f"Report saved to {filename}")
    return filename  # ← return path