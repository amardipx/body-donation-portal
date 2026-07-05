import os
from fastapi import BackgroundTasks
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

load_dotenv()

env = Environment(
    loader=FileSystemLoader("app/templates/emails")
)

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

    message.add_alternative(body, subtype = "html")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(message)

def send_witness_verification(background_tasks: BackgroundTasks, witness_email: str, witness_name: str, verification_link: str):
    subject = "Witness Verification Required"
    
    template = env.get_template("witness_verification.html")
    
    body = template.render(witness_name = witness_name, verification_link = verification_link )
    
    background_tasks.add_task(send_email, witness_email, subject, body)

def send_donor_confirmation(background_tasks: BackgroundTasks, donor_email: str, donor_name: str):
    subject = "Body Donation Registration Completed"
    
    template = env.get_template("donor_confirmation.html")
    
    body = template.render(donor_name = donor_name)
    
    background_tasks.add_task(send_email, donor_email, subject, body)
        