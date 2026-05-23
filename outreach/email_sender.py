"""Email sending infrastructure using SMTP."""
import os
import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """SMTP configuration."""
    smtp_server: str
    smtp_port: int
    email_address: str
    email_password: str
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            email_address=os.getenv("SMTP_EMAIL", ""),
            email_password=os.getenv("SMTP_PASSWORD", ""),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        )

    def is_configured(self) -> bool:
        return bool(self.email_address and self.email_password)


@dataclass
class EmailResult:
    """Result of sending an email."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    sent_at: Optional[datetime] = None


class EmailSender:
    """Handles email sending via SMTP."""

    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig.from_env()

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_name: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> EmailResult:
        """Send an email via SMTP."""
        if not self.config.is_configured():
            return EmailResult(
                success=False,
                error="SMTP not configured. Set SMTP_EMAIL and SMTP_PASSWORD in .env",
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{from_name or self.config.email_address} <{self.config.email_address}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain", "utf-8"))
            if html_body:
                msg.attach(MIMEText(html_body, "html", "utf-8"))

            if attachments:
                for filepath in attachments:
                    self._attach_file(msg, filepath)

            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls(context=context)
                server.login(self.config.email_address, self.config.email_password)
                server.send_message(msg)

            message_id = msg.get("Message-ID", "")
            logger.info(f"Email sent to {to_email}: {subject}")
            return EmailResult(
                success=True,
                message_id=message_id,
                sent_at=datetime.utcnow(),
            )

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return EmailResult(success=False, error=f"Authentication failed: {e}")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return EmailResult(success=False, error=f"SMTP error: {e}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return EmailResult(success=False, error=str(e))

    def _attach_file(self, msg: MIMEMultipart, filepath: str):
        """Attach a file to the email."""
        with open(filepath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(filepath)}",
            )
            msg.attach(part)

    def send_batch(
        self,
        emails: List[Dict[str, Any]],
        delay_seconds: float = 2.0,
    ) -> List[EmailResult]:
        """Send multiple emails with delay between each."""
        import time
        results = []
        for email_data in emails:
            result = self.send_email(
                to_email=email_data["to"],
                subject=email_data["subject"],
                body=email_data["body"],
                html_body=email_data.get("html_body"),
                from_name=email_data.get("from_name"),
                attachments=email_data.get("attachments"),
            )
            results.append(result)
            if delay_seconds > 0:
                time.sleep(delay_seconds)
        return results
