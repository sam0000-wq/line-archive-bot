import base64
from nacl import encoding, public

public_key_b64 = "6YyCFSGgGEx6vot5y3l3FVNOn+bKmOsgddN46jhi9RE="
public_key = public.PublicKey(base64.b64decode(public_key_b64), encoding.RawEncoder())
sealed_box = public.SealedBox(public_key)

secrets = {
    "GMAIL_USER": "itsamliu2025@gmail.com",
    "GMAIL_APP_PASSWORD": "uulfdwvlldolvlhw",
    "REPORT_TO_EMAIL": "itsamliu2025@gmail.com"
}

for name, value in secrets.items():
    encrypted = sealed_box.encrypt(value.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")
    print(f'{name}: "{encrypted_b64}"')