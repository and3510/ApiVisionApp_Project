from sqlalchemy import TIMESTAMP, Column, Date, DateTime, ForeignKey, Integer, String, Boolean, Text
from config.database import SspBase, CinBase

class FichaCriminal(SspBase):
    __tablename__ = "ficha_criminal"

    cpf = Column(String(14), primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    ficha_criminal = Column(Text)
    foragido = Column(Boolean, default=False)


class Usuario(SspBase):

    __tablename__ = "usuarios"

    matricula = Column(String(20), primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    nome_social = Column(String(255))
    nome_mae = Column(String(255), nullable=False)
    nome_pai = Column(String(255), nullable=False)
    data_nascimento = Column(String(30), nullable=False)
    cpf = Column(String(1), nullable=False)
    telefone = Column(String(15), nullable=False)
    sexo = Column(String(1), nullable=False)
    nacionalidade = Column(String(100), nullable=False)
    naturalidade = Column(String(100), nullable=False)
    tipo_sanguineo = Column(String(5))
    cargo = Column(String(100), nullable=False)
    nivel_classe = Column(String(50), nullable=False)
    senha = Column(String(255), nullable=False)
    id_usuario = Column(String(30), nullable=False)
    data_criacao_conta = Column(TIMESTAMP, nullable=False)

class Identidade(CinBase):
    __tablename__ = "identidade"

    cpf = Column(String(14), primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    nome_mae = Column(String(100))
    vetor_facial = Column(String)

class Pessoa_Alerta(CinBase):
    __tablename__ = "pessoa_alerta"

    id_alerta = Column(String(30), primary_key=True, index=True)
    cpf = Column(String(11), nullable=False)
    matricula = Column(String(20), nullable=False)


class Mensagens_Alerta(CinBase):
    __tablename__ = "mensagens_alerta"

    id_mensagem = Column(String(30), primary_key=True, index=True)
    id_alerta = Column(String(30), nullable=False)
    data_mensagem = Column(String(20), nullable=False)  
    conteudo_mensagem = Column(String, nullable=False)
    matricula = Column(String(20), nullable=False)
    localizacao = Column(String, nullable=False)
    cpf = Column(String(11), nullable=False)