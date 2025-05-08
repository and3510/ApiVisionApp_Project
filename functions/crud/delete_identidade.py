
from fastapi import Depends, HTTPException

from typing import Annotated
from sqlalchemy.orm import Session

from config.database import SspCriminososBase

from functions.dependencias import get_ssp_criminosos_db
import config.models as models
from config.database import ssp_criminosos_engine



ssp_criminosos_db_dependency = Annotated[Session, Depends(get_ssp_criminosos_db)]


SspCriminososBase.metadata.create_all(bind=ssp_criminosos_engine)

def delete_identidade(cpf: str, db: ssp_criminosos_db_dependency):
    # Verificar se a identidade existe
    identidade = db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="Identidade não encontrada.")

    # Buscar a ficha criminal associada
    ficha = db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()

    if ficha:
        # Remover os crimes associados à ficha criminal
        try:
            db.query(models.Crime).filter(models.Crime.id_ficha == ficha.id_ficha).delete()
            # Remover a ficha criminal
            db.delete(ficha)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Erro ao remover os dados associados: " + str(e))

    # Remover a identidade
    try:
        db.delete(identidade)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao remover a identidade: " + str(e))

    return {"message": "Identidade e dados associados removidos com sucesso."}