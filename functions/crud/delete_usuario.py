

from fastapi import Depends, HTTPException

from typing import Annotated
from sqlalchemy.orm import Session

from config.database import CinBase

from functions.dependencias import get_cin_db
import config.models as models
from config.database import cin_engine
from firebase_admin import auth


cin_db_dependency = Annotated[Session, Depends(get_cin_db)]

CinBase.metadata.create_all(bind=cin_engine)

def delete_usuario(matricula: str, db: cin_db_dependency):
    # Recuperar o usuário do banco de dados usando matrícula
    db_usuario = db.query(models.Usuario).filter(models.Usuario.matricula == matricula).first()
    alertas_usuario = db.query(models.Mensagens_Alerta).filter(models.Mensagens_Alerta.matricula == matricula).all()
    usuario_noAlerta = db.query(models.Pessoa_Alerta).filter(models.Pessoa_Alerta.matricula == matricula).all()

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

    if alertas_usuario:
        for alerta in alertas_usuario:
            db.delete(alerta)

    if usuario_noAlerta:
        for alerta in usuario_noAlerta:
            db.delete(alerta)

    db.delete(db_usuario)
    db.commit()

    return {"message": "Usuário removido com sucesso."}