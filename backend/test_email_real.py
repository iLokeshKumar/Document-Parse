from app.utils import send_email
from app.config import SMTP_USER

if __name__ == "__main__":
    print(f"Testing email with user: {SMTP_USER}")
    send_email(SMTP_USER, "Test Email", "This is a test email to verify credentials.")
