import secrets
import string

def generate_random_password(full_name: str, length: int = 6) -> str:
    
    first_name = full_name.split()[0].capitalize()
    random_part = "".join(
        secrets.choice(string.digits)
        for _ in range(length)
    )
    
    return f"{first_name}@{random_part}"