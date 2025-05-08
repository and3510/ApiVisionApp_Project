
from fastapi import Depends, HTTPException

from typing import Annotated
from sqlalchemy.orm import Session

from config.database import SspCriminososBase

from functions.dependencias import get_ssp_criminosos_db
import config.models as models
from config.database import ssp_criminosos_engine



ssp_criminosos_db_dependency = Annotated[Session, Depends(get_ssp_criminosos_db)]


SspCriminososBase.metadata.create_all(bind=ssp_criminosos_engine)


async def delete_identidade(cpf: str, db: ssp_criminosos_db_dependency):
    # Verificar se a identidade existe
    identidade = db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="Identidade não encontrada.")
    
    ficha = db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()

    
    crimes = db.query(models.Crime).filter(models.Crime.id_ficha == ficha.id_ficha).all()

    if crimes:
        # Remover os crimes associados
        for crime in crimes:
            db.delete(crime)

    if ficha:
        # Remover a ficha criminal associada
        db.delete(ficha)
    


    # Remover a identidade
    db.delete(identidade)
    db.commit()

    return {"message": "Identidade e dados associados removidos com sucesso."}