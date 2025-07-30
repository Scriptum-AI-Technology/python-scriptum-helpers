from google.oauth2 import id_token
from google.auth.transport import requests as requests

from parse import parse
import os


def current_user(bearer):
    token = parse("Bearer {token}", bearer)
    idinfo = id_token.verify_oauth2_token(
        token["token"],
        requests.Request(),
        os.getenv("CLIENT_ID", "").split(",")
    )
    return idinfo

def authenticate(event, key="sub"):
    try:
        request = event["http"]
        headers = request["headers"]
        idinfo = current_user(headers["authorization"])
    except Exception as ex:
        return None, str(ex)

    return idinfo.get(key, idinfo), None
