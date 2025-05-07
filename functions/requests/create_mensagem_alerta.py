
# ----------- Bibliotecas -----------



from fastapi import Depends, HTTPException
from typing import Annotated
import pytz
from sqlalchemy.orm import Session
from config.database import SspBase, CinBase
from functions.dependencias import get_ssp_db, get_cin_db
import config.models as models
from config.database import ssp_engine, cin_engine

ssp_db_dependency = Annotated[Session, Depends(get_ssp_db)]
cin_db_dependency = Annotated[Session, Depends(get_cin_db)]

SspBase.metadata.create_all(bind=ssp_engine)
CinBase.metadata.create_all(bind=cin_engine)



def create_mensagem_alerta(
    db: ssp_db_dependency,
    db1: cin_db_dependency,
    cpf: str,
    conteudo_mensagem: str,
    matricula: str,
    localizacao: str
):

    from uuid import uuid4
    from datetime import datetime

    # Função para gerar um ID com no máximo 20 caracteres
    def generate_short_uuid():
        return str(uuid4()).replace("-", "")[:20]

    # Verifica se o CPF existe na tabela Identidade
    identidade = db1.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Identidade.")

    # Verifica se a matrícula existe na tabela Usuario
    usuario = db1.query(models.Usuario).filter(models.Usuario.matricula == matricula).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada na tabela Usuario.")

    # Verifica se o CPF já existe na tabela Pessoa_Alerta
    pessoa_alerta = db.query(models.Pessoa_Alerta).filter(models.Pessoa_Alerta.cpf == cpf).first()

    if pessoa_alerta:
        # Reutiliza o id_alerta existente
        id_alerta = pessoa_alerta.id_alerta
    else:
        id_alerta = generate_short_uuid()  # Gera um novo ID com no máximo 20 caracteres
        nova_pessoa_alerta = models.Pessoa_Alerta(
            id_alerta=id_alerta,
            cpf=cpf,
            matricula=matricula
        )
        db.add(nova_pessoa_alerta)
        db.commit()
        db.refresh(nova_pessoa_alerta)

    br_tz = pytz.timezone('America/Sao_Paulo')

    nova_mensagem = models.Mensagens_Alerta(
        id_mensagem=generate_short_uuid(),  # Gera um novo ID com no máximo 20 caracteres
        id_alerta=id_alerta,
        data_mensagem=datetime.now(br_tz).strftime("%H:%M:%S %d/%m/%Y"),  # Data atual
        conteudo_mensagem=conteudo_mensagem,
        matricula=matricula,
        localizacao=localizacao,
        cpf=cpf
    )
    db.add(nova_mensagem)
    db.commit()
    db.refresh(nova_mensagem)

    return nova_mensagem
