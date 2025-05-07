

from datetime import datetime
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


def create_usuario(
    db: cin_db_dependency,
    matricula: str,
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
    
    check_identidade = db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()

    if check_identidade:
        nome = check_identidade.nome
        nome_mae = check_identidade.nome_mae
        nome_pai = check_identidade.nome_pai
        data_nascimento = check_identidade.data_nascimento

    else:
        return {"error": "Identidade não encontrada."}
    
    # CPF como "e-mail" fake para Firebase (não é bonito, mas funciona)
    fake_email = f"{cpf}@app.com"

    # Cria o usuário no Firebase Authentication
    try:
        user = auth.create_user(
            email=fake_email,
            password=senha,
            display_name=nome,
            disabled=False
        )
    except auth.EmailAlreadyExistsError:
        return {"error": "Usuário já existe no Firebase"}

    # Agora cria também no seu banco de dados local
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
        senha=senha,
        id_usuario=user.uid,  # Usa o UID gerado pelo Firebase
        data_criacao_conta=datetime.utcnow()
    )
    db.add(db_usuario)

    try: db.commit()

    except Exception as e:
        # Revogar os tokens do usuário no Firebase (invalida o JWT atual)
        auth.revoke_refresh_tokens(db_usuario.id_usuario)

        # Agora sim, deletar o usuário do Firebase
        auth.delete_user(db_usuario.id_usuario)
        raise HTTPException(status_code=500, detail=f"Erro ao remover usuário do Firebase: {str(e)}")
    
    db.refresh(db_usuario)

    return db_usuario
