from fastapi import Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from config.database import SspUsuarioBase
from functions.dependencias import get_ssp_usuario_db
import config.models as models
from config.database import ssp_usuario_engine
from functions.auth_utils import verify_token



ssp_usuario_db_dependency = Annotated[Session, Depends(get_ssp_usuario_db)]

SspUsuarioBase.metadata.create_all(bind=ssp_usuario_engine)


def perfil_usuario(
    db: ssp_usuario_db_dependency,
    user_data: dict = Depends(verify_token),
):
    # Pega o id_usuario (uid) do token
    id_usuario = user_data.get("sub")

    # Busca o usuário no banco
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "nome": usuario.nome,
        "cargo": usuario.cargo,
        "matricula": usuario.matricula,
        "nivel_classe": usuario.nivel_classe
    }