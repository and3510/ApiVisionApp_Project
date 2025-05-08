# ----------- Bibliotecas -----------


import json
from fastapi import HTTPException

import os

from firebase_admin import auth
from jose import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()


def auth_with_firebase(token_data: str):
    try:
        decoded_token = auth.verify_id_token(token_data)
        user_id = decoded_token["uid"]

        expire = datetime.utcnow() + timedelta(minutes=1440)
        jwt_payload = {
            "sub": user_id,
            "exp": expire
        }
        jwt_token = jwt.encode(jwt_payload, os.getenv("SECRET_KEY"), algorithm="HS256")

        return {"access_token": jwt_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=401, detail="Token Firebase inválido ou expirado")

