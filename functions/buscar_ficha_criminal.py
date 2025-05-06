from fastapi import Depends, HTTPException
from typing import Annotated
from sqlalchemy.orm import Session
from config.database import CinBase, SspBase
from functions.dependencias import get_ssp_db, get_cin_db
import config.models as models
from config.database import ssp_engine, cin_engine


ssp_db_dependency = Annotated[Session, Depends(get_ssp_db)]
cin_db_dependency = Annotated[Session, Depends(get_cin_db)]

SspBase.metadata.create_all(bind=ssp_engine)
CinBase.metadata.create_all(bind=cin_engine)


def buscar_ficha_criminal(cpf: str, identidade_db: cin_db_dependency, ficha_db: ssp_db_dependency):
    # Verificar se o CPF existe na tabela Identidade
    identidade = identidade_db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Identidade.")

    # Verificar se o CPF possui ficha criminal
    ficha_criminal = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    crimes = []
    if ficha_criminal:
        crimes = ficha_db.query(models.Crime).filter(models.Crime.id_ficha == ficha_criminal.id_ficha).all()

    # Buscar todos os alertas relacionados ao CPF
    alertas = identidade_db.query(models.Mensagens_Alerta).filter(models.Mensagens_Alerta.cpf == cpf).all()
    alertas_formatados = [
        {
            "id_alerta": alerta.id_alerta,
            "id_mensagem": alerta.id_mensagem,
            "data_mensagem": alerta.data_mensagem,
            "conteudo_mensagem": alerta.conteudo_mensagem,
            "matricula": alerta.matricula,
            "localizacao": alerta.localizacao,
        }
        for alerta in alertas
    ]

    # Construir a resposta
    resposta = {
        "cpf": identidade.cpf,
        "nome": identidade.nome,
        "nome_mae": identidade.nome_mae,
        "nome_pai": identidade.nome_pai,
        "data_nascimento": identidade.data_nascimento,
        "foto_url": identidade.url_face,
        "ficha_criminal": {
            "id_ficha": ficha_criminal.id_ficha if ficha_criminal else None,
            "vulgo": ficha_criminal.vulgo if ficha_criminal else None,
            "foragido": ficha_criminal.foragido if ficha_criminal else None,
        },
        "crimes": [
            {
                "id_crime": crime.id_crime,
                "nome_crime": crime.nome_crime,
                "artigo": crime.artigo,
                "descricao": crime.descricao,
                "cidade": crime.cidade,
                "estado": crime.estado,
                "status": crime.status,
            }
            for crime in crimes
        ],
        "alertas": alertas_formatados,
    }

    return resposta