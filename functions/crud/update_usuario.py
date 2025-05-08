
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



def update_usuario(
    matricula: str,
    db: ssp_usuario_db_dependency,
    nome: str = None,
    nome_social: str = None,
    nome_mae: str = None,
    nome_pai: str = None,
    data_nascimento: str = None,
    cpf: str = None,
    telefone: str = None,
    sexo: str = None,
    nacionalidade: str = None,
    naturalidade: str = None,
    tipo_sanguineo: str = None,
    cargo: str = None,
    nivel_classe: str = None,
    senha: str = None
):
    # Recuperar o usuário do banco de dados usando matrícula
    db_usuario = db.query(models.Usuario).filter(models.Usuario.matricula == matricula).first()
    
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    # Atualiza os campos apenas se forem fornecidos
    if nome:
        db_usuario.nome = nome
    if nome_social:
        db_usuario.nome_social = nome_social
    if nome_mae:
        db_usuario.nome_mae = nome_mae
    if nome_pai:
        db_usuario.nome_pai = nome_pai
    if data_nascimento:
        db_usuario.data_nascimento = data_nascimento
    if cpf:
        db_usuario.cpf = cpf
    if telefone:
        db_usuario.telefone = telefone
    if sexo:
        db_usuario.sexo = sexo
    if nacionalidade:
        db_usuario.nacionalidade = nacionalidade
    if naturalidade:
        db_usuario.naturalidade = naturalidade
    if tipo_sanguineo:
        db_usuario.tipo_sanguineo = tipo_sanguineo
    if cargo:
        db_usuario.cargo = cargo
    if nivel_classe:
        db_usuario.nivel_classe = nivel_classe
    if senha:
        db_usuario.senha = senha
        try:
            # Atualizar a senha no Firebase
            auth.update_user(
                db_usuario.id_usuario,  # UID do usuário no Firebase
                password=senha
            )
            print("Senha atualizada no Firebase com sucesso.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar senha no Firebase: {str(e)}")

    db.commit()
    db.refresh(db_usuario)

    return db_usuario