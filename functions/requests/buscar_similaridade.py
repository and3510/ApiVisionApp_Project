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
    mais_similar = similaridades[0]

    LIMIAR_CONFIANTE = 0.4
    LIMIAR_AMBÍGUO = 0.5

    # Buscar ficha criminal associada ao CPF
    cpf = mais_similar["cpf"]
    ficha_criminal = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    crimes = []
    if ficha_criminal:
        crimes = ficha_db.query(models.Crime).filter(models.Crime.id_ficha == ficha_criminal.id_ficha).all()

    ficha_criminal_info = {
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
                "cidade": crime.cidade,
                "estado": crime.estado,
                "status": crime.status
            }
            for crime in crimes
        ]
    }

    

    if mais_similar["distancia"] < LIMIAR_CONFIANTE:
        return JSONResponse(content={
            "status": "confiante",
            "identidade": mais_similar,
            "ficha_criminal": ficha_criminal_info,
        })

    elif mais_similar["distancia"] < LIMIAR_AMBÍGUO:
        segunda_mais_similar = similaridades[1] if len(similaridades) > 1 else None
        
        # Buscar ficha criminal do mais similar
        ficha_criminal_mais_similar = None
        if mais_similar:
            ficha_criminal_1 = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == mais_similar["cpf"]).first()
            crimes_1 = []
            if ficha_criminal_1:
                crimes_1 = ficha_db.query(models.Crime).filter(models.Crime.id_ficha == ficha_criminal_1.id_ficha).all()
            ficha_criminal_mais_similar = {
                "ficha_criminal": {
                    "id_ficha": ficha_criminal_1.id_ficha,
                    "vulgo": ficha_criminal_1.vulgo
                } if ficha_criminal_1 else None,
                "crimes": [
                    {
                        "id_crime": crime.id_crime,
                        "nome_crime": crime.nome_crime,
                        "artigo": crime.artigo,
                        "descricao": crime.descricao,
                        "cidade": crime.cidade,
                        "estado": crime.estado,
                        "status": crime.status
                    }
                    for crime in crimes_1
                ]
            }

        # Buscar ficha criminal do segundo mais similar
        ficha_criminal_segundo_similar = None
        if segunda_mais_similar:
            ficha_criminal_2 = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == segunda_mais_similar["cpf"]).first()
            crimes_2 = []
            if ficha_criminal_2:
                crimes_2 = ficha_db.query(models.Crime).filter(models.Crime.id_ficha == ficha_criminal_2.id_ficha).all()
            ficha_criminal_segundo_similar = {
                "ficha_criminal": {
                    "id_ficha": ficha_criminal_2.id_ficha,
                    "vulgo": ficha_criminal_2.vulgo
                } if ficha_criminal_2 else None,
                "crimes": [
                    {
                        "id_crime": crime.id_crime,
                        "nome_crime": crime.nome_crime,
                        "artigo": crime.artigo,
                        "descricao": crime.descricao,
                        "cidade": crime.cidade,
                        "estado": crime.estado,
                        "status": crime.status
                    }
                    for crime in crimes_2
                ]
            }

        return JSONResponse(content={
            "status": "ambíguo",
            "mais_proximas": [mais_similar, segunda_mais_similar],
            "ficha_criminal_mais_similar": ficha_criminal_mais_similar,
            "ficha_criminal_segundo_similar": ficha_criminal_segundo_similar,
        })

    else:
        return JSONResponse(content={
            "status": "nenhuma similaridade forte",
        })