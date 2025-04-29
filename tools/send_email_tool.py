# tools/send_email_tool.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
#done
load_dotenv()

def send_email(to: str = None, subject: str = None, body: str = None, **kwargs):
    """Send an email with subject and body to the specified recipient."""
    try:
        # Check if parameters are nested in a 'parameters' key
        if 'parameters' in kwargs and isinstance(kwargs['parameters'], dict):
            # Extract nested parameters if present
            params = kwargs['parameters']
            to = params.get('to', to)
            subject = params.get('subject', subject)
            body = params.get('body', body)
        
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8')) 

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        return {"status": "success", "message": f"Email sent to {to}"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}