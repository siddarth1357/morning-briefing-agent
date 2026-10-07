# delivery/slack_sender.py
import json
import urllib.request
import config


def send_slack(brief):
    """
    Posts the brief to a Slack Incoming Webhook.
    Disabled by default. Returns True on success, False otherwise (never raises).
    """
    if not config.SLACK_ENABLED:
        print("  [slack] Disabled. Skipping.")
        return False

    if not config.SLACK_WEBHOOK_URL:
        print("  [slack] Missing SLACK_WEBHOOK_URL in .env. Skipping.")
        return False

    try:
        payload = json.dumps({"text": brief}).encode("utf-8")
        request = urllib.request.Request(
            config.SLACK_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            ok = response.status == 200
        if ok:
            print("  [slack] ✅ Sent")
        else:
            print(f"  [slack] ✗ HTTP {response.status}")
        return ok
    except Exception as e:
        print(f"  [slack] ✗ Failed: {e}")
        return False
