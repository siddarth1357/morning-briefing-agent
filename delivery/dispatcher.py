# delivery/dispatcher.py
from delivery.email_sender import send_email
from delivery.slack_sender import send_slack


def deliver_brief(brief):
    """
    Runs all enabled delivery channels.
    Returns a results dict: {"email": bool, "slack": bool}.
    """
    print("\n--- STEP 7: DELIVERING BRIEF ---")
    results = {
        "slack": send_slack(brief),
        "email": send_email(brief),
    }
    print(f"--- DELIVERY COMPLETE : {results} ---")
    return results
