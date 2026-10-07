# delivery/email_sender.py
import html
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import config


def _inline(text):
    """Escapes HTML, then applies Markdown links, bold, and italics."""
    text = html.escape(text, quote=True)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    return text


def markdown_to_html(markdown_text):
    """
    Converts the brief's Markdown into simple, safe HTML for email:
    headings, unordered lists, paragraphs, links, bold/italic.
    """
    out = []
    in_list = False

    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()
        is_item = stripped.startswith(("- ", "* "))

        # Close an open list when a non-list line appears
        if in_list and not is_item:
            out.append("</ul>")
            in_list = False

        if not stripped:
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = min(max(len(heading.group(1)), 2), 5)
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            continue

        if is_item:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(stripped[2:])}</li>")
            continue

        out.append(f"<p>{_inline(stripped)}</p>")

    if in_list:
        out.append("</ul>")

    return "\n".join(out)


def send_email(brief):
    """
    Sends the brief as a multipart (plain + HTML) email via Gmail SMTP.
    Returns True on success, False otherwise (never raises).
    """
    if not config.EMAIL_ENABLED:
        print("  [email] Disabled. Skipping.")
        return False

    if not all([config.EMAIL_FROM, config.EMAIL_TO, config.EMAIL_APP_PASSWORD]):
        print("  [email] Missing EMAIL_FROM / EMAIL_TO / EMAIL_APP_PASSWORD in .env. Skipping.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = config.BRIEFING_SUBJECT
        msg["From"] = config.EMAIL_FROM
        msg["To"] = config.EMAIL_TO

        # Plain-text fallback (the raw Markdown) + styled HTML version
        msg.attach(MIMEText(brief, "plain", "utf-8"))
        html_body = (
            '<html><body style="font-family:-apple-system,Segoe UI,Roboto,'
            'Helvetica,Arial,sans-serif;line-height:1.5;color:#1a1a1a;max-width:680px;">'
            + markdown_to_html(brief)
            + "</body></html>"
        )
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # App passwords work without spaces ("abcd efgh..." -> "abcdefgh...")
        password = (config.EMAIL_APP_PASSWORD or "").replace(" ", "")

        # Primary: implicit TLS (port 465). Fallback: STARTTLS (port 587)
        # for networks/firewalls that block 465.
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
                server.login(config.EMAIL_FROM, password)
                server.sendmail(config.EMAIL_FROM, [config.EMAIL_TO], msg.as_string())
        except (smtplib.SMTPException, OSError):
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
                server.starttls()
                server.login(config.EMAIL_FROM, password)
                server.sendmail(config.EMAIL_FROM, [config.EMAIL_TO], msg.as_string())

        print(f"  [email] ✅ Sent to {config.EMAIL_TO}")
        return True

    except Exception as e:
        print(f"  [email] ✗ Failed: {e}")
        return False
