import base64
from nacl import encoding, public

public_key_b64 = "6YyCFSGgGEx6vot5y3l3FVNOn+bKmOsgddN46jhi9RE="
public_key = public.PublicKey(base64.b64decode(public_key_b64), encoding.RawEncoder())
sealed_box = public.SealedBox(public_key)

secrets = {
    "LINE_CHANNEL_ACCESS_TOKEN": "cCchQly0oKnd/kSJRDo+F473GupP7Ezd0aTQT7Ry8cfjUZTnceXQ98Ij9p2pkFQFh8n3mnimoD6GT8/0SklLJaz5wDovbOtONjRrxzJbkcq4MsMUAX0opLqabjngJ4pblrkaH+DR+QFPS7CO2efUCQdB04t89/1O/w1cDnyilFU=",
    "TARGET_GROUP_ID": "Ca6bb09334a9a5febb3d5d5a8affba5a9"
}

for name, value in secrets.items():
    encrypted = sealed_box.encrypt(value.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")
    print(f'{name}: "{encrypted_b64}"')