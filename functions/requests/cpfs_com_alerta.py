from fastapi import Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from config.database import CinBase
from functions.dependencias import get_cin_db
import config.models as models
from config.database import cin_engine



cin_db_dependency = Annotated[Session, Depends(get_cin_db)]

CinBase.metadata.create_all(bind=cin_engine)



def cpfs_com_alerta(db: cin_db_dependency):
    # Consulta todos os registros na tabela Pessoa_Alerta
    pessoas_alerta = db.query(models.Pessoa_Alerta).all()

    if not pessoas_alerta:
        raise HTTPException(status_code=404, detail="Nenhum alerta encontrado.")

    # Agrupa os CPFs, conta a quantidade de alertas e busca o nome da pessoa
    alertas_por_cpf = {}
    for pessoa_alerta in pessoas_alerta:
        cpf = pessoa_alerta.cpf

        if cpf in alertas_por_cpf:
            alertas_por_cpf[cpf]["quantidade"] += 1
        else:
            # Busca o nome da pessoa na tabela Identidade
            identidade = db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
            nome = identidade.nome if identidade else "Nome não encontrado"
            url_face = identidade.url_face if identidade else "URL não encontrada"
            alertas_por_cpf[cpf] = {"quantidade": 1, "nome": nome}

    # Formata a resposta
    resposta = [
        {"url_face": url_face, "cpf": cpf, "nome": dados["nome"], "quantidade_alertas": dados["quantidade"]}
        for cpf, dados in alertas_por_cpf.items()
    ]

    return {"alertas": resposta}