import json
from fastapi import Depends, HTTPException, UploadFile, File
from typing import Annotated
from sqlalchemy.orm import Session
import shutil
import os
import face_recognition
from fastapi.responses import JSONResponse
import numpy as np
from config.database import SspCriminososBase, SspUsuarioBase
from functions.clahe import aplicar_clahe
from functions.dependencias import get_ssp_criminosos_db, get_ssp_usuario_db
import config.models as models
from config.database import ssp_criminosos_engine, ssp_usuario_engine
from uuid import uuid4
from datetime import datetime
import pytz 


ssp_criminosos_db_dependency = Annotated[Session, Depends(get_ssp_criminosos_db)]

SspCriminososBase.metadata.create_all(bind=ssp_criminosos_engine)

ssp_usuario_db_dependency = Annotated[Session, Depends(get_ssp_usuario_db)]

SspUsuarioBase.metadata.create_all(bind=ssp_usuario_engine)


def buscar_similaridade(
    matricula: str,
    ficha_db: ssp_criminosos_db_dependency,
    user_db: ssp_usuario_db_dependency,
    file: UploadFile = File(...)
):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Processar a imagem com CLAHE
    imagem = aplicar_clahe(temp_file)
    encodings = face_recognition.face_encodings(imagem, num_jitters=10, model="large")
    os.remove(temp_file)

    if not encodings:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado.")

    vetor_facial = encodings[0]
    identidades = ficha_db.query(models.Identidade).all()
    if not identidades:
        raise HTTPException(status_code=404, detail="Nenhuma identidade encontrada no banco de dados.")

    usuario = user_db.query(models.Usuario).filter(models.Usuario.matricula == matricula).first()

    br_tz = pytz.timezone('America/Sao_Paulo')

    similaridades = []
    for identidade in identidades:
        vetor_facial_banco = np.array(json.loads(identidade.vetor_facial))
        distancia = np.linalg.norm(vetor_facial - vetor_facial_banco)
        similaridades.append({
            "cpf": identidade.cpf,
            "nome": identidade.nome,
            "nome_mae": identidade.nome_mae,
            "nome_pai": identidade.nome_pai,
            "data_nascimento": identidade.data_nascimento,
            "url_face": identidade.url_facial,
            "gemeo": identidade.gemeo,
            "distancia": distancia,
        })

    similaridades.sort(key=lambda x: x["distancia"])

    LIMIAR_CONFIANTE = 0.4
    LIMIAR_AMBÍGUO = 0.5
    ambiguos = [p for p in similaridades if p["distancia"] < LIMIAR_AMBÍGUO]

    log = models.Log_Resultado_Reconhecimento(
        id_ocorrido=str(uuid4()).replace("-", "")[:30],
        matricula=usuario.matricula,
        id_usuario=usuario.id_usuario,
        distancia=str(round(similaridades[0]["distancia"], 4)),
        cpf=similaridades[0]["cpf"] if similaridades else None,
        id_ficha=None,  # Será preenchido abaixo, se existir
        status_reconhecimento="nenhuma similaridade forte",
        data_ocorrido=datetime.now(br_tz).strftime("%H:%M:%S %d/%m/%Y"),
        url_facial_referencia=similaridades[0]["url_face"] if similaridades else None
    )

    if ambiguos and ambiguos[0]["distancia"] < LIMIAR_CONFIANTE:
        identidade_confiante = ambiguos[0]
        ficha_criminal_info = buscar_ficha_criminal_completa(ficha_db, identidade_confiante["cpf"])
        log.status_reconhecimento = "confiante"
        log.cpf = identidade_confiante["cpf"]
        log.url_facial_referencia = identidade_confiante["url_face"]

        if ficha_criminal_info["ficha_criminal"]:
            log.id_ficha = ficha_criminal_info["ficha_criminal"]["id_ficha"]

        user_db.add(log)
        user_db.commit()
        user_db.refresh(log)

        return JSONResponse(content={
            "status": "confiante",
            "identidade": identidade_confiante,
            "ficha_criminal": ficha_criminal_info,
        })

    elif len(ambiguos) > 0:
        log.status_reconhecimento = "ambíguo"
        log.cpf = ambiguos[0]["cpf"]
        log.url_facial_referencia = ambiguos[0]["url_face"]

        ficha_criminal_info = buscar_ficha_criminal_completa(ficha_db, ambiguos[0]["cpf"])
        if ficha_criminal_info["ficha_criminal"]:
            log.id_ficha = ficha_criminal_info["ficha_criminal"]["id_ficha"]

        user_db.add(log)
        user_db.commit()
        user_db.refresh(log)

        resultados_ambiguos = []
        for identidade in ambiguos:
            ficha_criminal_info = buscar_ficha_criminal_completa(ficha_db, identidade["cpf"])
            resultados_ambiguos.append({
                "identidade": identidade,
                "ficha_criminal": ficha_criminal_info
            })

        return JSONResponse(content={
            "status": "ambíguo",
            "possiveis_identidades": resultados_ambiguos
        })

    else:
        user_db.add(log)
        user_db.commit()
        user_db.refresh(log)

        menor_distancia = similaridades[0]["distancia"] if similaridades else None
        return JSONResponse(content={
            "status": "nenhuma similaridade forte",
            "menor_distancia": menor_distancia
        })

    

def buscar_ficha_criminal_completa(ficha_db, cpf):
    ficha_criminal = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    crimes = []
    if ficha_criminal:
        crimes = ficha_db.query(models.Crime).filter(models.Crime.id_ficha == ficha_criminal.id_ficha).all()
    return {
        "ficha_criminal": {
            "id_ficha": ficha_criminal.id_ficha,
            "vulgo": ficha_criminal.vulgo
        } if ficha_criminal else None,
        "crimes": [
            {
                "id_crime": crime.id_crime,
                "nome_crime": crime.nome_crime,
                "artigo": crime.artigo,
                "descricao": crime.descricao,
                "data_ocorrencia": crime.data_ocorrencia,
                "cidade": crime.cidade,
                "estado": crime.estado,
                "status": crime.status
            }
            for crime in crimes
        ]
    }

