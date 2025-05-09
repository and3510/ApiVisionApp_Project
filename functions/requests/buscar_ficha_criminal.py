from fastapi import Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from config.database import SspCriminososBase
from functions.dependencias import get_ssp_criminosos_db
import config.models as models
from config.database import ssp_criminosos_engine


ssp_criminosos_db_dependency = Annotated[Session, Depends(get_ssp_criminosos_db)]

SspCriminososBase.metadata.create_all(bind=ssp_criminosos_engine)



def buscar_ficha_criminal(cpf: str, ficha_db: ssp_criminosos_db_dependency):
    # Verificar se o CPF existe na tabela Identidade
    identidade = ficha_db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Identidade.")

    # Verificar se o CPF possui ficha criminal
    ficha_criminal = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    crimes = []
    if ficha_criminal:
        crimes = ficha_db.query(models.Crime).filter(models.Crime.id_ficha == ficha_criminal.id_ficha).all()


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
            "vulgo": ficha_criminal.vulgo if ficha_criminal else None,
        },
        "crimes": [
            {
                "id_crime": crime.id_crime,
                "nome_crime": crime.nome_crime,
                "artigo": crime.artigo,
                "descricao": crime.descricao,
                "cidade": crime.cidade,
                "estado": crime.estado,
                "status": crime.status,
            }
            for crime in crimes
        ]
    }

    return resposta