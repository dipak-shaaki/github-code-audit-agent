import os
import requests

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

def send_to_slack(repo_name, pr_number, report_path, risk_level="UNKNOWN"):
    """Send summary message + upload full report file to Slack."""

    risk_emoji = {
        "HIGH": "🔴",
        "MEDIUM": "🟡",
        "LOW": "🟢",
        "UNKNOWN": "⚪"
    }.get(risk_level, "⚪")

    # read report
    try:
        with open(report_path, "r") as f:
            report_content = f.read()
    except:
        report_content = "Report file not found."

    # extract top 3 issues — lines containing "Issue" or "Function:"
    lines = report_content.split("\n")
    issues = [l for l in lines if "Function:" in l or "### Issue" in l][:3]
    top_issues = "\n".join(issues) if issues else "See full report."

    # step 1 — send summary message
    message_payload = {
        "channel": SLACK_CHANNEL_ID,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔍 PR Audit Report — {repo_name}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Repository:*\n`{repo_name}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*PR Number:*\n#{pr_number}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Risk Level:*\n{risk_emoji} {risk_level}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Issues Found:*\n{top_issues}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Full report attached below 👇"
                }
            }
        ]
    }

    msg_response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={
            "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
            "Content-Type": "application/json"
        },
        json=message_payload
    )

    if msg_response.json().get("ok"):
        print(f"  Slack summary sent for {repo_name} PR #{pr_number}")
    else:
        print(f"  Slack message failed: {msg_response.json().get('error')}")

    # step 2 — upload full report file
    with open(report_path, "rb") as f:
        file_response = requests.post(
            "https://slack.com/api/files.upload",
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
            data={
                "channels": SLACK_CHANNEL_ID,
                "filename": f"{repo_name.replace('/', '_')}_pr_{pr_number}.md",
                "title": f"Full Audit Report — {repo_name} PR #{pr_number}",
                "initial_comment": f"Complete audit report for PR #{pr_number}"
            },
            files={"file": f}
        )

    if file_response.json().get("ok"):
        print(f"  Report file uploaded to Slack")
    else:
        print(f"  File upload failed: {file_response.json().get('error')}")