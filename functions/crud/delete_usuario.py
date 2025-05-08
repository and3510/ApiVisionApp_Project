

from fastapi import Depends, HTTPException

from typing import Annotated
from sqlalchemy.orm import Session

from config.database import SspUsuarioBase

from functions.dependencias import get_ssp_usuario_db
import config.models as models
from config.database import ssp_usuario_engine
from firebase_admin import auth



ssp_usuario_db_dependency = Annotated[Session, Depends(get_ssp_usuario_db)]

SspUsuarioBase.metadata.create_all(bind=ssp_usuario_engine)


def delete_usuario(matricula: str, db: ssp_usuario_db_dependency):
    # Recuperar o usuário do banco de dados usando matrícula
    db_usuario = db.query(models.Usuario).filter(models.Usuario.matricula == matricula).first()

    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    try:
        # Revogar os tokens do usuário no Firebase (invalida o JWT atual)
        auth.revoke_refresh_tokens(db_usuario.id_usuario)

        # Agora sim, deletar o usuário do Firebase
        auth.delete_user(db_usuario.id_usuario)
    except auth.UserNotFoundError:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover usuário do Firebase: {str(e)}")

    # Remover o usuário do banco de dados


    db.delete(db_usuario)
    db.commit()

    return {"message": "Usuário removido com sucesso."}