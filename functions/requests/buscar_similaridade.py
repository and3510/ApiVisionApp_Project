import json
from fastapi import Depends, HTTPException, UploadFile, File
from typing import Annotated
from sqlalchemy.orm import Session
import shutil
import os
import face_recognition
from fastapi.responses import JSONResponse
import numpy as np
from config.database import SspCriminososBase
from functions.clahe import aplicar_clahe
from functions.dependencias import get_ssp_criminosos_db
import config.models as models
from config.database import ssp_criminosos_engine


ssp_criminosos_db_dependency = Annotated[Session, Depends(get_ssp_criminosos_db)]

SspCriminososBase.metadata.create_all(bind=ssp_criminosos_engine)


def buscar_similaridade(
    ficha_db: ssp_criminosos_db_dependency,
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
            "distancia": distancia,
        })

    # Ordena pela menor distância
    similaridades.sort(key=lambda x: x["distancia"])

    # Define os limiares
    LIMIAR_CONFIANTE = 0.4
    LIMIAR_AMBÍGUO = 0.5

    # Filtra os candidatos ambíguos
    ambiguos = [p for p in similaridades if p["distancia"] < LIMIAR_AMBÍGUO]

    # Caso 1: Confiança Alta (menor que limiar confiante)
    if ambiguos and ambiguos[0]["distancia"] < LIMIAR_CONFIANTE:
        identidade_confiante = ambiguos[0]
        ficha_criminal_info = buscar_ficha_criminal_completa(ficha_db, identidade_confiante["cpf"])
        return JSONResponse(content={
            "status": "confiante",
            "identidade": identidade_confiante,
            "ficha_criminal": ficha_criminal_info,
        })

    # Caso 2: Ambiguidade (um ou mais abaixo do limiar ambíguo, mas nenhum confiável)
    elif len(ambiguos) > 0:
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

    # Caso 3: Nenhuma similaridade aceitável
    else:
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

