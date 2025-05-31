

from datetime import datetime
from fastapi import Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session

from config.database import SspUsuarioBase
from functions.dependencias import get_ssp_usuario_db
import config.models as models
from config.database import ssp_usuario_engine
from firebase_admin import auth
from passlib.context import CryptContext



ssp_usuario_db_dependency = Annotated[Session, Depends(get_ssp_usuario_db)]

SspUsuarioBase.metadata.create_all(bind=ssp_usuario_engine)



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_usuario(
    db: ssp_usuario_db_dependency,
    matricula: str,
    nome: str,
    nome_mae: str,
    nome_pai: str,
    data_nascimento: str,
    cpf: str,
    telefone: str,
    sexo: str,
    nacionalidade: str,
    naturalidade: str,
    tipo_sanguineo: str,
    cargo: str,
    nivel_classe: str,
    senha: str,
    nome_social: str = None
):
    fake_email = f"{cpf}@app.com"

    try:
        user = auth.create_user(
            email=fake_email,
            password=senha,
            display_name=nome,
            disabled=False
        )
    except auth.EmailAlreadyExistsError:
        return {"error": "Usuário já existe no Firebase"}

    hashed_password = pwd_context.hash(senha)

    db_usuario = models.Usuario(
        matricula=matricula,
        nome=nome,
        nome_social=nome_social,
        nome_mae=nome_mae,
        nome_pai=nome_pai,
        data_nascimento=data_nascimento,
        cpf=cpf,
        telefone=telefone,
        sexo=sexo,
        nacionalidade=nacionalidade,
        naturalidade=naturalidade,
        tipo_sanguineo=tipo_sanguineo,
        cargo=cargo,
        nivel_classe=nivel_classe,
        senha=hashed_password,
        id_usuario=user.uid,
        data_criacao_conta=datetime.utcnow()
    )
    db.add(db_usuario)

    try:
        db.commit()
    except Exception as e:
        auth.revoke_refresh_tokens(db_usuario.id_usuario)
        auth.delete_user(db_usuario.id_usuario)
        raise HTTPException(status_code=500, detail=f"Erro ao remover usuário do Firebase: {str(e)}")
    
    db.refresh(db_usuario)
    return db_usuario
