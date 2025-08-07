from typing import List, Optional
from flask import current_app, render_template
from flask_mail import Message
from app import mail


def _is_email_configured() -> bool:
    """Return True if minimal mail settings are present."""
    return bool(
        current_app.config.get("MAIL_SERVER")
        and current_app.config.get("MAIL_DEFAULT_SENDER")
    )


def send_email(
    subject: str,
    recipients: List[str],
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """
    Send an email using Flask-Mail. Returns True if the send was attempted and
    no exception was raised. If email is not configured, returns False.
    """
    if not _is_email_configured():
        # In dev/test environments without email config, skip sending.
        current_app.logger.info("Email not sent: MAIL configuration missing")
        return False

    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
        )
        if text_body:
            msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as exc:  # pragma: no cover - logging side effect
        current_app.logger.exception("Failed to send email: %s", exc)
        return False


def send_approval_email(job, confirmation_url: str) -> bool:
    """
    Send the student an approval email with a confirmation link.
    """
    subject = "3D Print Job Approved - Confirm to Proceed"
    text_body = (
        f"Hello {job.student_name},\n\n"
        "Your 3D print job has been approved. Please confirm to proceed: "
        f"{confirmation_url}\n\n"
        "If you did not request this, please ignore this email."
    )
    try:
        html_body = render_template(
            "email/approval_email.html",
            job=job,
            confirmation_url=confirmation_url,
        )
    except Exception:
        html_body = (
            f"<p>Hello {job.student_name},</p>"
            "<p>Your 3D print job has been approved.</p>"
            f"<p><a href=\"{confirmation_url}\">Click here to confirm your job</a></p>"
            "<p>If you did not request this, please ignore this email.</p>"
        )
    return send_email(subject, [job.student_email], html_body, text_body)


def send_status_update_email(job, new_status: str) -> bool:
    """
    Send a basic status update email to the student.
    """
    subject = f"3D Print Job Status Updated: {new_status.title()}"
    text_body = (
        f"Hello {job.student_name},\n\n"
        f"The status of your 3D print job has changed to: {new_status}.\n\n"
        "This is an automated notification."
    )
    try:
        html_body = render_template(
            "email/submission_status.html",
            job=job,
            status=new_status,
        )
    except Exception:
        html_body = (
            f"<p>Hello {job.student_name},</p>"
            f"<p>The status of your 3D print job has changed to: <strong>{new_status}</strong>.</p>"
            "<p>This is an automated notification.</p>"
        )
    return send_email(subject, [job.student_email], html_body, text_body)


