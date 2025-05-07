

from fastapi import Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session

from config.database import SspBase

from functions.dependencias import get_ssp_db
import config.models as models
from config.database import ssp_engine

ssp_db_dependency = Annotated[Session, Depends(get_ssp_db)]

SspBase.metadata.create_all(bind=ssp_engine)



def update_ficha(
    db: ssp_db_dependency,
    cpf: str,
    vulgo: str = None,
    foragido: bool = None,
):
    # Verifica se a ficha criminal existe para o CPF fornecido
    ficha_criminal = db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    if not ficha_criminal:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Ficha Criminal.")

    # Atualiza os campos apenas se forem fornecidos
    if vulgo is not None:
        ficha_criminal.vulgo = vulgo
    if foragido is not None:
        ficha_criminal.foragido = foragido

    # Salva as alterações no banco de dados
    db.commit()
    db.refresh(ficha_criminal)

    return {
        "message": "Ficha criminal atualizada com sucesso.",
        "ficha_criminal": {
            "id_ficha": ficha_criminal.id_ficha,
            "cpf": ficha_criminal.cpf,
            "vulgo": ficha_criminal.vulgo,
            "foragido": ficha_criminal.foragido,
        }
    }
    