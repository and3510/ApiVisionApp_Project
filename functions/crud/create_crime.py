

from enum import Enum
from fastapi import Depends, HTTPException

from typing import Annotated
from sqlalchemy.orm import Session

from uuid import uuid4
from config.database import SspCriminososBase
from functions.dependencias import get_ssp_criminosos_db
import config.models as models
from config.database import ssp_criminosos_engine


ssp_criminosos_db_dependency = Annotated[Session, Depends(get_ssp_criminosos_db)]


SspCriminososBase.metadata.create_all(bind=ssp_criminosos_engine)


class CrimeStatus(str, Enum):
    investigando = "Em Aberto"
    foragido = "Foragido"

def create_crime(
    db: ssp_criminosos_db_dependency,
    cpf: str,
    nome_crime: str,
    artigo: str,
    descricao: str,
    data_ocorrencia: str,
    cidade: str,
    estado: str,
    status: CrimeStatus,
    vulgo: str = None,
):


    # Verifica se o CPF existe na tabela Identidade
    identidade = db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Identidade.")

    # Verifica se existe uma ficha criminal associada ao CPF
    ficha_criminal = db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    if not ficha_criminal:
        # Cria uma nova ficha criminal se não existir
        ficha_criminal = models.FichaCriminal(
            id_ficha=str(uuid4()).replace("-", "")[:30],  # Trunca o UUID para 30 caracteres
            cpf=cpf,
            vulgo=vulgo,  # Valor padrão para vulgo
            foragido=False  # Valor padrão para foragido
        )
        db.add(ficha_criminal)
        db.commit()
        db.refresh(ficha_criminal)
        

    # Cria o novo registro de crime
    novo_crime = models.Crime(
        id_crime=str(uuid4()).replace("-", "")[:30],  # Trunca o UUID para 30 caracteres
        id_ficha=ficha_criminal.id_ficha,  # Usa o id_ficha da ficha criminal correspondente
        nome_crime=nome_crime,
        artigo=artigo,
        descricao=descricao,
        data_ocorrencia=data_ocorrencia,
        cidade=cidade,
        estado=estado,
        status=status
    )
    db.add(novo_crime)
    db.commit()
    db.refresh(novo_crime)

    return {
        "id_crime": novo_crime.id_crime,
        "id_ficha": novo_crime.id_ficha,
        "cpf": ficha_criminal.cpf,
        "nome_crime": novo_crime.nome_crime,
        "artigo": novo_crime.artigo,
        "descricao": novo_crime.descricao,
        "data_ocorrencia": novo_crime.data_ocorrencia,
        "cidade": novo_crime.cidade,
        "estado": novo_crime.estado,
        "status": novo_crime.status,
        "vulgo": ficha_criminal.vulgo,
    }
