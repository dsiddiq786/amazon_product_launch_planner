import logging
from typing import Any, Dict, Optional
from pathlib import Path
import emails
from emails.template import JinjaTemplate
from jinja2 import Environment, FileSystemLoader

from app.config.settings import settings


def send_email(
    email_to: str,
    subject: str,
    html_template: str,
    environment: Dict[str, Any] = {}
) -> bool:
    """
    Send an email using the configured SMTP server
    
    Args:
        email_to: The recipient's email address
        subject: The email subject
        html_template: The HTML template name (from the templates directory)
        environment: Variables to pass to the template
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    if not settings.SMTP_HOST or not settings.EMAILS_FROM_EMAIL:
        logging.warning("SMTP not configured, skipping email")
        return False
    
    # Templates directory
    templates_dir = Path(__file__).parent.parent / "templates"
    jinja_env = Environment(
        loader=FileSystemLoader(templates_dir)
    )
    template = jinja_env.get_template(html_template)
    html_content = template.render(**environment)
    
    message = emails.Message(
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL)
    )
    
    smtp_options = {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "tls": settings.SMTP_TLS
    }
    
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        smtp_options["user"] = settings.SMTP_USER
        smtp_options["password"] = settings.SMTP_PASSWORD
    
    response = message.send(to=email_to, smtp=smtp_options)
    logging.info(f"Email sent to {email_to}, status: {response.status_code}")
    
    return response.status_code in [250]


def send_verification_email(email_to: str, token: str) -> bool:
    """
    Send email verification link
    
    Args:
        email_to: The recipient's email address
        token: Verification token
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    subject = f"{settings.PROJECT_NAME} - Verify Your Email"
    verification_url = f"/verify-email?token={token}"
    
    return send_email(
        email_to=email_to,
        subject=subject,
        html_template="email_verification.html",
        environment={
            "project_name": settings.PROJECT_NAME,
            "verification_url": verification_url,
            "email": email_to
        }
    )


def send_reset_password_email(email_to: str, token: str) -> bool:
    """
    Send password reset link
    
    Args:
        email_to: The recipient's email address
        token: Password reset token
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    subject = f"{settings.PROJECT_NAME} - Password Reset"
    reset_url = f"/reset-password?token={token}"
    
    return send_email(
        email_to=email_to,
        subject=subject,
        html_template="password_reset.html",
        environment={
            "project_name": settings.PROJECT_NAME,
            "reset_url": reset_url,
            "email": email_to
        }
    )


def send_invitation_email(email_to: str, invited_by: str, token: str) -> bool:
    """
    Send invitation to join the platform
    
    Args:
        email_to: The recipient's email address
        invited_by: Name or email of the person sending the invitation
        token: Invitation token
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    subject = f"{settings.PROJECT_NAME} - You're Invited"
    invitation_url = f"/accept-invitation?token={token}"
    
    return send_email(
        email_to=email_to,
        subject=subject,
        html_template="invitation.html",
        environment={
            "project_name": settings.PROJECT_NAME,
            "invitation_url": invitation_url,
            "email": email_to,
            "invited_by": invited_by
        }
    ) 