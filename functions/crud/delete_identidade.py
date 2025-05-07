
from fastapi import Depends, HTTPException

from typing import Annotated
from sqlalchemy.orm import Session

from config.database import CinBase

from functions.crud.delete_usuario import delete_usuario
from functions.dependencias import get_cin_db
import config.models as models
from config.database import cin_engine



cin_db_dependency = Annotated[Session, Depends(get_cin_db)]


CinBase.metadata.create_all(bind=cin_engine)


async def delete_identidade(cpf: str, db: cin_db_dependency):
    # Verificar se a identidade existe
    identidade = db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="Identidade não encontrada.")

    # Verificar se a identidade está associada a um usuário
    usuario = db.query(models.Usuario).filter(models.Usuario.cpf == cpf).first()
    if usuario:
        # Reutilizar a função delete_usuario para remover o usuário e seus dados associados
        await delete_usuario(usuario.matricula, db)

    # Remover a identidade
    db.delete(identidade)
    db.commit()

    return {"message": "Identidade e dados associados removidos com sucesso."}