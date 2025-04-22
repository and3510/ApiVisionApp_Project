from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Security
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session
import shutil
import os
import face_recognition
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import numpy as np
from fastapi.security.api_key import APIKeyHeader
from database import (
    FichaSessionLocal,
    IdentidadeSessionLocal
)
from functions.root import root
from functions.auth_api_key import verificar_api_key
import models as models
import cv2  


app = FastAPI()

# ----------- Pydantic Models -----------

class FichaCriminalBase(BaseModel):
    cpf: str
    ficha_criminal: str
    foragido: bool = False

# ----------- Dependências -----------

def get_ficha_db():
    db = FichaSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_identidade_db():
    db = IdentidadeSessionLocal()
    try:
        yield db
    finally:
        db.close()

ficha_db_dependency = Annotated[Session, Depends(get_ficha_db)]
identidade_db_dependency = Annotated[Session, Depends(get_identidade_db)]

# ----------- Função de Melhoria de Imagem -----------

def aplicar_clahe(imagem_path):
    imagem_bgr = cv2.imread(imagem_path)
    lab = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    final = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
    return final

# ---------- Rotas -----------

@app.get("/")
async def get_root():
    return await root()


@app.post("/ficha_criminal/", dependencies=[Depends(verificar_api_key)])
async def create_ficha_criminal(ficha: FichaCriminalBase, db: ficha_db_dependency, identidade_db: identidade_db_dependency):
    cpf_existente = identidade_db.query(models.Identidade).filter(models.Identidade.cpf == ficha.cpf).first()
    if not cpf_existente:
        raise HTTPException(status_code=400, detail="CPF não encontrado na tabela Identidade.")
    db_ficha = models.FichaCriminal(
        cpf=ficha.cpf,
        nome="Nome não informado",
        ficha_criminal=ficha.ficha_criminal,
        foragido=ficha.foragido
    )
    db.add(db_ficha)
    db.commit()
    db.refresh(db_ficha)
    return db_ficha

@app.post("/identidade/", dependencies=[Depends(verificar_api_key)])
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


@app.post("/buscar_similaridade/", dependencies=[Depends(verificar_api_key)])
async def buscar_similaridade(
    db: identidade_db_dependency,
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

    mais_similar = min(similaridades, key=lambda x: x["distancia"])
    LIMITE_SIMILARIDADE = 0.5
    if mais_similar["distancia"] > LIMITE_SIMILARIDADE:
        return JSONResponse(content={
            "detail": "Nenhuma identidade similar encontrada.",
            "mais_proxima": mais_similar
        })

    return JSONResponse(content=mais_similar)
