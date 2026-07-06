import os
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
from datetime import datetime
from weasyprint import HTML
from supabase import create_client, Client
import secrets

load_dotenv()

env = Environment(
    loader=FileSystemLoader("app/templates/certificates")
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)

def _generate_certificate_number() -> str:
    year = datetime.now().year
    random_suffix = secrets.token_hex(3).upper()

    return f"BDP-{year}-{random_suffix}"

def _render_template(donor_name: str, certificate_number: str, issued_date: str,):
    
    template = env.get_template("consent_certificate.html")

    return template.render(
        donor_name=donor_name,
        certificate_number=certificate_number,
        issued_date=issued_date,
    )

def _upload_certificate(pdf_bytes: bytes, certificate_number: str):
    
    storage_path = f"certificates/consent/{certificate_number}.pdf"
    
    try:
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=pdf_bytes,
            file_options={
                "content-type": "application/pdf"
            },
        )
    except Exception as e:
        raise RuntimeError(
            f"Certificate upload failed: {e}"
        )

    return storage_path



def generate_consent_certificate(donor_name: str):
    
    certificate_number = _generate_certificate_number()
    issued_date = datetime.now().strftime("%d %B %Y")
    
    html = _render_template(donor_name = donor_name, certificate_number = certificate_number, issued_date = issued_date,)
    
    pdf_buffer = BytesIO()
    
    HTML(string= html).write_pdf(pdf_buffer)
        
    pdf_bytes = pdf_buffer.getvalue()
    
    storage_path = _upload_certificate(pdf_bytes, certificate_number)
    
    return certificate_number, storage_path



if __name__ == "__main__":
    certificate_number, storage_path = generate_consent_certificate(
        donor_name="Vivek Mandal"
    )

    print(certificate_number)
    print(storage_path)