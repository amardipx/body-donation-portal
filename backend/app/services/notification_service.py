import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    raise RuntimeError("Email configurations not configured")

def send_email(reciever_email: str, subject: str, body: str):

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = EMAIL_ADDRESS
    message["To"] = reciever_email

    message.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(message)

def send_witness_verification(witness_email: str, witness_name: str, verification_link: str):
    subject = "Witness Verification Required"
    body = f"""
Hello {witness_name},
You have been listed as a witness for a body donation consent.
Please verify your consent by visiting the link below:
{verification_link}

Thank you.
Body Donation Portal.
"""
    
    send_email(witness_email, subject, body)

def send_donor_confirmation(donor_email: str, donor_name: str):
    subject = "Body Donation Registration Completed"

    body = f"""
Hello {donor_name}, 
Your body donation consent has been successfully verified.
Both listed witnesses have confirmed their consent.
Your registration is now active.

Thank you,
Body Donation Portal
"""
    send_email(donor_email, subject, body)
        