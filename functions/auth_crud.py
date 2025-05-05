import os
from fastapi.security import APIKeyHeader
from fastapi import HTTPException, Security

# Define o cabeçalho esperado
api_key_header = APIKeyHeader(name="minhaChave", auto_error=False)

async def verify_crud_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Acesso negado: chave de API inválida.")