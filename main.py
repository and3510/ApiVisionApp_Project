# ----------- Bibliotecas -----------


from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Security
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session
import shutil
import os
import face_recognition
from fastapi.responses import JSONResponse
import numpy as np
from fastapi.security.api_key import APIKeyHeader
from functions.clahe import aplicar_clahe
from functions.dependencias import get_ficha_db, get_identidade_db
from functions.auth_api_key import verificar_api_key
import models as models
from firebase_admin import credentials, auth, initialize_app
from jose import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta
from auth_utils import verify_token  # ou de jwt_auth, se renomear

load_dotenv()

# 🔧 Inicializar Firebase Admin
cred = credentials.Certificate("firebase_config.json")
initialize_app(cred)

# ----------- Carregar variáveis de ambiente -----------
app = FastAPI()


# ----------- Dependências -----------


ficha_db_dependency = Annotated[Session, Depends(get_ficha_db)]
identidade_db_dependency = Annotated[Session, Depends(get_identidade_db)]



# ---------- Rotas -----------


class FirebaseToken(BaseModel):
    firebase_token: str


@app.get("/usuario/perfil")
def perfil_usuario(user_data: dict = Depends(verify_token)):
    return {"mensagem": "Bem-vindo!", "usuario": user_data.get("sub")}

@app.post("/auth/firebase")
def auth_with_firebase(token_data: FirebaseToken):
    try:
        decoded_token = auth.verify_id_token(token_data.firebase_token)
        user_id = decoded_token["uid"]

        expire = datetime.utcnow() + timedelta(minutes=60)
        jwt_payload = {
            "sub": user_id,
            "exp": expire
        }
        jwt_token = jwt.encode(jwt_payload, os.getenv("SECRET_KEY"), algorithm="HS256")

        return {"access_token": jwt_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=401, detail="Token Firebase inválido ou expirado")


@app.post("/create-ficha_criminal/", dependencies=[Depends(verify_token)])
async def create_ficha_criminal(db: ficha_db_dependency,  identidade_db: identidade_db_dependency, cpf: str, ficha_criminal: str, foragido: bool = False):
    cpf_existente = identidade_db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not cpf_existente:
        raise HTTPException(status_code=400, detail="CPF não encontrado na tabela Identidade.")
    db_ficha = models.FichaCriminal(
        cpf=cpf,
        nome="Nome não informado",
        ficha_criminal=ficha_criminal,
        foragido=foragido
    )
    db.add(db_ficha)
    db.commit()
    db.refresh(db_ficha)
    return db_ficha


@app.post("/create-identidade/", dependencies=[Depends(verify_token)])
async def create_identidade(
    db: identidade_db_dependency,
    cpf: str,
    nome: str,
    nome_mae: str,
    file: UploadFile = File(...)
):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    imagem = aplicar_clahe(temp_file)  # <--- Imagem tratada com CLAHE
    encodings = face_recognition.face_encodings(imagem)
    os.remove(temp_file)

    if not encodings:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado.")

    vetor_facial = encodings[0]
    vetor_facial_reduzido = [round(float(x), 5) for x in vetor_facial[:]]

    db_identidade = models.Identidade(
        cpf=cpf,
        nome=nome,
        nome_mae=nome_mae,
        vetor_facial=vetor_facial_reduzido
    )
    db.add(db_identidade)
    db.commit()
    db.refresh(db_identidade)

    return {
        "cpf": db_identidade.cpf,
        "nome": db_identidade.nome,
        "nome_mae": db_identidade.nome_mae,
        "vetor_facial": vetor_facial_reduzido
    }


@app.post("/buscar_similaridade_foto/", dependencies=[Depends(verify_token)])
async def buscar_similaridade(
    db: identidade_db_dependency,
    file: UploadFile = File(...)
):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    imagem = aplicar_clahe(temp_file)  # Imagem tratada com CLAHE
    encodings = face_recognition.face_encodings(imagem)
    os.remove(temp_file)

    if not encodings:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado.")

    vetor_facial = encodings[0]
    identidades = db.query(models.Identidade).all()
    if not identidades:
        raise HTTPException(status_code=404, detail="Nenhuma identidade encontrada no banco de dados.")

    similaridades = []
    for identidade in identidades:
        vetor_facial_banco = np.array(eval(identidade.vetor_facial))
        distancia = np.linalg.norm(vetor_facial - vetor_facial_banco)
        similaridades.append({
            "cpf": identidade.cpf,
            "nome": identidade.nome,
            "nome_mae": identidade.nome_mae,
            "distancia": distancia
        })

    # Ordena pela menor distância
    similaridades.sort(key=lambda x: x["distancia"])
    mais_similar = similaridades[0]

    LIMIAR_CONFIANTE = 0.3
    LIMIAR_AMBÍGUO = 0.5

    if mais_similar["distancia"] < LIMIAR_CONFIANTE:
        return JSONResponse(content={
            "status": "confiante",
            "identidade": mais_similar
        })

    elif mais_similar["distancia"] < LIMIAR_AMBÍGUO:
        segunda_mais_similar = similaridades[1] if len(similaridades) > 1 else None
        return JSONResponse(content={
            "status": "ambíguo",
            "mais_proximas": [mais_similar, segunda_mais_similar]
        })

    else:
        return JSONResponse(content={
            "status": "nenhuma similaridade forte",
            "mais_proxima": mais_similar
        })


@app.get("/buscar_ficha_criminal/{cpf}", dependencies=[Depends(verificar_api_key)])
async def buscar_ficha_criminal(cpf: str, identidade_db: identidade_db_dependency, ficha_db: ficha_db_dependency):
    # Verificar se o CPF existe na tabela Identidade
    identidade = identidade_db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Identidade.")

    # Verificar se o CPF possui ficha criminal
    ficha_criminal = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()

    # Construir a resposta
    resposta = {
        "cpf": identidade.cpf,
        "nome": identidade.nome,
        "nome_mae": identidade.nome_mae,
    }

    if ficha_criminal:
        resposta["ficha_criminal"] = ficha_criminal.ficha_criminal
        resposta["foragido"] = ficha_criminal.foragido

    return resposta