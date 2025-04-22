import os

from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = os.getenv("API_KEY_NAME")


api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


# ----------- Função para autenticação da API Key -----------

async def verificar_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: API Key inválida."
        )