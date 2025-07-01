import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from media_manager.notification.config import EmailConfig

log = logging.getLogger(__name__)

def send_email(html: str, addressee: str, subject: str|list[str]) -> None:
    email_conf = EmailConfig()
    message = MIMEMultipart()
    message["From"] = email_conf.from_email
    message["To"] = addressee
    message["Subject"] = str(subject)
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP(email_conf.smtp_host, email_conf.smtp_port) as server:
        if email_conf.use_tls:
            server.starttls()
        server.login(email_conf.smtp_user, email_conf.smtp_password)
        server.sendmail(email_conf.from_email,addressee, message.as_string())

    log.info(f"Successfully sent email to {addressee} with subject: {subject}")


