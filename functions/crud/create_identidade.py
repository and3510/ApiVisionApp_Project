# ----------- Bibliotecas -----------


import json
from fastapi import Depends, HTTPException, UploadFile, File

from typing import Annotated
from sqlalchemy.orm import Session
import shutil
import os

import face_recognition

from config.database import SspCriminososBase
from functions.clahe import aplicar_clahe
from functions.dependencias import get_ssp_criminosos_db
import config.models as models
from config.database import ssp_criminosos_engine
from functions.minio import upload_to_minio




ssp_criminosos_db_dependency = Annotated[Session, Depends(get_ssp_criminosos_db)]


SspCriminososBase.metadata.create_all(bind=ssp_criminosos_engine)



def create_identidade(
    db: ssp_criminosos_db_dependency,
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
    db_ficha = models.Identidade(
        cpf=cpf,
        nome=nome,
        nome_pai=nome_pai,
        nome_mae=nome_mae,
        data_nascimento=data_nascimento,
        vetor_facial=json.dumps(vetor_facial_reduzido),
        url_facial=url  # Armazena a URL gerada pelo MinIO
    )
    db.add(db_ficha)
    db.commit()
    db.refresh(db_ficha)

    return {
        "cpf": db_ficha.cpf,
        "nome": db_ficha.nome,
        "nome_mae": db_ficha.nome_mae,
        "nome_pai": db_ficha.nome_pai,
        "data_nascimento": db_ficha.data_nascimento,
        "vetor_facial": vetor_facial_reduzido,
        "foto_url": db_ficha.url_facial  # Retorna a URL da foto
    }