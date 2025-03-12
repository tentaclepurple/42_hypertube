# backend/app/services/email_service.py


import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_password_reset_email(to_email, reset_url):

    smtp_server = os.environ.get("MAIL_SERVER")
    smtp_port = int(os.environ.get("MAIL_PORT", 587))
    smtp_user = os.environ.get("MAIL_USERNAME")
    smtp_password = os.environ.get("MAIL_PASSWORD")
    from_email = os.environ.get("FROM_EMAIL")
    
    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = "Reset Your Password - Hypertube"
    
    body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>You requested a password reset for your Hypertube account.</p>
        <p>Click the link below to set a new password:</p>
        <p><a href="{reset_url}">Reset Your Password</a></p>
        <p>This link is valid for 5 minutes.</p>
        <p>If you didn't request this reset, please ignore this email.</p>
    </body>
    </html>
    """
    
    message.attach(MIMEText(body, "html"))
    
    try:
        print("Sending email...", smtp_server, smtp_port, smtp_user, flush=True)
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)
        server.quit()
        print(f"Password reset email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False