import secrets
import string

def generate_random_password(full_name: str, length: int = 6) -> str:
    name_part = full_name.strip().split()
    
    if name_part[0].lower().rstrip(".") in {
       "dr",
        "mr",
        "mrs",
        "ms",
        "miss",
    }:
        name_part.pop(0)
    
    first_name = name_part[0].capitalize()
    random_part = "".join(
        secrets.choice(string.digits)
        for _ in range(length)
    )
    
    return f"{first_name}@{random_part}"