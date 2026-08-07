import os
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
import requests
import smtplib
from email.message import EmailMessage
from supabase import create_client, Client

load_dotenv()

env = Environment(
    loader=FileSystemLoader("app/templates/emails")
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    raise RuntimeError("Email configurations not configured")


BREVO_API_KEY = os.getenv("BREVO_API_KEY")


def send_email(recipient, subject, html_body):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": "Body Donation Portal",
            "email": EMAIL_ADDRESS
        },
        "to": [
            {"email": recipient}
        ],
        "subject": subject,
        "htmlContent": html_body
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()


# def send_email(reciever_email: str, subject: str, body: str):
#     message = EmailMessage()

#     message["Subject"] = subject
#     message["From"] = EMAIL_ADDRESS
#     message["To"] = reciever_email

#     message.add_alternative(body, subtype = "html")

#     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#         server.starttls()
#         server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
#         server.send_message(message)


def send_witness_verification(witness_email: str, witness_name: str, verification_link: str):
    subject = "Witness Verification Required"
    
    template = env.get_template("witness_verification.html")
    
    body = template.render(witness_name = witness_name, verification_link = verification_link )
    
    send_email(witness_email, subject, body)

def send_donor_confirmation(donor_email: str, donor_name: str, storage_path: str):
    
    signed_url = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(storage_path,86400)
    
    certificate_link = (signed_url.get("signedURL") or signed_url.get("signedUrl"))

    subject = "Body Donation Registration Completed"
    
    template = env.get_template("donor_confirmation.html")
    
    body = template.render(donor_name = donor_name, certificate_link = certificate_link )
    
    send_email(donor_email, subject, body)

def send_family_assigned_staff(
    family_member_email: str, 
    family_member_name: str,
    donor_name: str, 
    institution_name: str,
    institution_phone: str,
    staff_name: str,
    staff_phone: str,
    staff_email: str,
):
    subject = "Body Donation - Death Report Received"
    
    template = env.get_template("family_death_report.html")
    
    body = template.render(
        family_member_name = family_member_name, 
        donor_name = donor_name,
        institution_name = institution_name, 
        institution_phone = institution_phone, 
        staff_name = staff_name,
        staff_phone = staff_phone,
        staff_email =staff_email,
    )
    
    send_email(family_member_email, subject, body)