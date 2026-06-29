"""
Email sending abstraction.

In development (EMAIL_BACKEND=console) all emails are printed to stdout.
In production (EMAIL_BACKEND=smtp) emails are sent via STARTTLS SMTP.

Switch by setting EMAIL_BACKEND in .env — no code changes needed.
"""
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


# ── Templates ─────────────────────────────────────────────────────────────────

def _verification_body(display_name: str | None, link: str) -> tuple[str, str]:
    name = display_name or "NYU student"
    plain = f"Hi {name},\n\nVerify your NYU Bites account:\n{link}\n\nThis link expires in {settings.verification_token_expire_hours} hours."
    html = f"""
    <p>Hi <strong>{name}</strong>,</p>
    <p>Thanks for signing up for <strong>NYU Bites</strong> — your hub for student discounts near campus.</p>
    <p><a href="{link}" style="background:#5c0a0a;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;">Verify my email</a></p>
    <p>Or copy this link:<br><code>{link}</code></p>
    <p>Expires in {settings.verification_token_expire_hours} hours.</p>
    """
    return plain, html


def _reset_body(display_name: str | None, link: str) -> tuple[str, str]:
    name = display_name or "NYU student"
    plain = f"Hi {name},\n\nReset your NYU Bites password:\n{link}\n\nExpires in {settings.reset_token_expire_minutes} minutes. If you didn't request this, ignore this email."
    html = f"""
    <p>Hi <strong>{name}</strong>,</p>
    <p>We received a request to reset your <strong>NYU Bites</strong> password.</p>
    <p><a href="{link}" style="background:#5c0a0a;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;">Reset my password</a></p>
    <p>Or copy: <code>{link}</code></p>
    <p>Expires in {settings.reset_token_expire_minutes} minutes. If you didn't request this, you can safely ignore this email.</p>
    """
    return plain, html


# ── Backends ──────────────────────────────────────────────────────────────────

def _build_message(to: str, subject: str, plain: str, html: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.email_from_address}>"
    msg["To"] = to
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def _console_send(to: str, subject: str, plain: str) -> None:
    sep = "-" * 60
    print(f"\n{sep}\n[EMAIL] To: {to}\n[EMAIL] Subject: {subject}\n\n{plain}\n{sep}\n", flush=True)


def _smtp_send(to: str, subject: str, plain: str, html: str) -> None:
    msg = _build_message(to, subject, plain, html)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.email_from_address, to, msg.as_string())


async def _send(to: str, subject: str, plain: str, html: str) -> None:
    if settings.email_backend == "smtp":
        await asyncio.to_thread(_smtp_send, to, subject, plain, html)
    else:
        _console_send(to, subject, plain)


# ── Public API ────────────────────────────────────────────────────────────────

async def send_verification_email(to: str, display_name: str | None, token: str) -> None:
    link = f"{settings.frontend_url}/verify-email?token={token}"
    plain, html = _verification_body(display_name, link)
    await _send(to, "Verify your NYU Bites account", plain, html)


async def send_password_reset_email(to: str, display_name: str | None, token: str) -> None:
    link = f"{settings.frontend_url}/reset-password?token={token}"
    plain, html = _reset_body(display_name, link)
    await _send(to, "Reset your NYU Bites password", plain, html)
