from fastapi import Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from config.database import SspCriminososBase, SspUsuarioBase
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


def buscar_ficha_criminal(cpf: str, ficha_db: ssp_criminosos_db_dependency, user_db: ssp_usuario_db_dependency):
    # Verificar se o CPF existe na tabela Identidade
    identidade = ficha_db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Identidade.")

    # Verificar se o CPF possui ficha criminal
    ficha_criminal = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    crimes = []
    if ficha_criminal:
        crimes = ficha_db.query(models.Crime).filter(models.Crime.id_ficha == ficha_criminal.id_ficha).all()

    # usuario = user_db.query(models.Usuario).filter(models.Usuario.matricula == matricula).first()

    # br_tz = pytz.timezone('America/Sao_Paulo')

    
    # log_resultado_cpf = models.Log_Resultado_Cpf(
    #     id_entrada=str(uuid4()).replace("-", "")[:30],  # Gera um novo ID com no máximo 20 caracteres
    #     matricula=usuario.matricula,
    #     data_entrada_conta=datetime.now(br_tz).strftime("%H:%M:%S %d/%m/%Y"),  # Data atual
    #     cpf=ficha_criminal.cpf,
    #     id_usuario=usuario.id_usuario,
    #     id_ficha=ficha_criminal.id_ficha
    # )
    # db.add(log_resultado_cpf)
    # db.commit()
    # db.refresh(log_resultado_cpf)

    # Construir a resposta
    resposta = {
        "cpf": identidade.cpf,
        "nome": identidade.nome,
        "nome_mae": identidade.nome_mae,
        "nome_pai": identidade.nome_pai,
        "data_nascimento": identidade.data_nascimento,
        "foto_url": identidade.url_facial,
        "ficha_criminal": {
            "id_ficha": ficha_criminal.id_ficha if ficha_criminal else None,
            "vulgo": ficha_criminal.vulgo,
        },
        "crimes": [
            {
                "id_crime": crime.id_crime,
                "nome_crime": crime.nome_crime,
                "artigo": crime.artigo,
                "descricao": crime.descricao,
                "data_ocorrencia": crime.data_ocorrencia,
                "cidade": crime.cidade,
                "estado": crime.estado,
                "status": crime.status,
            }
            for crime in crimes
        ]
    }

    return resposta
