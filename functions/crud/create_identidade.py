# ----------- Bibliotecas -----------


import json
from fastapi import Depends, HTTPException, UploadFile, File

from typing import Annotated
from sqlalchemy.orm import Session
import shutil
import os

import face_recognition

from config.database import CinBase
from functions.clahe import aplicar_clahe
from functions.dependencias import get_cin_db
import config.models as models
from config.database import cin_engine
from functions.minio import upload_to_minio




cin_db_dependency = Annotated[Session, Depends(get_cin_db)]


CinBase.metadata.create_all(bind=cin_engine)



def create_identidade(
    db: cin_db_dependency,
    cpf: str,
    nome: str,
    nome_mae: str,
    nome_pai: str,
    data_nascimento: str,
    file: UploadFile = File(...)
):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Processar a imagem com CLAHE
    imagem = aplicar_clahe(temp_file)
    encodings = face_recognition.face_encodings(imagem, num_jitters=10, model="large")
    if not encodings:
        os.remove(temp_file)
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado.")

    # Fazer o upload da imagem para o MinIO
    bucket_name = "imagens"
    object_name = f"{cpf}.png"
    try:
        url = upload_to_minio(bucket_name, temp_file, object_name)
    except Exception as e:
        os.remove(temp_file)
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload para o MinIO: {str(e)}")

    # Remover o arquivo temporário
    os.remove(temp_file)

    # Reduzir o vetor facial
    vetor_facial = encodings[0]
    vetor_facial_reduzido = [round(float(x), 5) for x in vetor_facial[:]]

    # Criar o registro na tabela Identidade
    db_identidade = models.Identidade(
        cpf=cpf,
        nome=nome,
        nome_pai=nome_pai,
        nome_mae=nome_mae,
        data_nascimento=data_nascimento,
        vetor_facial=json.dumps(vetor_facial_reduzido),
        url_face=url  # Armazena a URL gerada pelo MinIO
    )
    db.add(db_identidade)
    db.commit()
    db.refresh(db_identidade)

    return {
        "cpf": db_identidade.cpf,
        "nome": db_identidade.nome,
        "nome_mae": db_identidade.nome_mae,
        "nome_pai": db_identidade.nome_pai,
        "data_nascimento": db_identidade.data_nascimento,
        "vetor_facial": vetor_facial_reduzido,
        "foto_url": db_identidade.url_face  # Retorna a URL da foto
    }