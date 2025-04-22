from sqlalchemy import Column, String, Boolean, Text
from database import FichaBase, IdentidadeBase

class FichaCriminal(FichaBase):
    __tablename__ = "ficha_criminal"

    cpf = Column(String(14), primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    ficha_criminal = Column(Text)
    foragido = Column(Boolean, default=False)

class Identidade(IdentidadeBase):
    __tablename__ = "identidade"

    cpf = Column(String(14), primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    nome_mae = Column(String(100))
    vetor_facial = Column(String)  