from sqlalchemy import TIMESTAMP, Column, Date, Integer, String, Boolean, Text
from config.database import SspCriminososBase, SspUsuarioBase


class Usuario(SspUsuarioBase):

    __tablename__ = "usuario"

    matricula = Column(String(10), primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    nome_social = Column(String(255))
    nome_mae = Column(String(255), nullable=False)
    nome_pai = Column(String(255), nullable=False)
    data_nascimento = Column(String(20), nullable=False)
    cpf = Column(String(14), nullable=False)
    telefone = Column(String(15), nullable=False)
    sexo = Column(String(5), nullable=False)
    nacionalidade = Column(String(100), nullable=False)
    naturalidade = Column(String(100), nullable=False)
    tipo_sanguineo = Column(String(5))
    cargo = Column(String(100), nullable=False)
    nivel_classe = Column(String(50), nullable=False)
    senha = Column(String(255), nullable=False)
    id_usuario = Column(String(50), nullable=False)
    data_criacao_conta = Column(TIMESTAMP, nullable=False)


class Log_Entrada(SspUsuarioBase):

    __tablename__ = "log_entrada"

    
    matricula = Column(String(10), primary_key=True, index=True)
    id_usuario = Column(String(50), nullable=False)
    cpf = Column(String(14), nullable=False)
    data_entrada_conta = Column(TIMESTAMP, nullable=False)


class Log_Resultado_Reconhecimento(SspUsuarioBase):
    __tablename__ = "log_resultado_reconhecimento"

    matricula = Column(String(10), primary_key=True, index=True)
    id_usuario = Column(String(50), nullable=False)
    distancia = Column(String(45), nullable=False)
    cpf = Column(String(14), nullable=True)
    nome_criminoso = Column(String(150), nullable=True)
    id_ficha = Column(String(30), nullable=True)
    status_reconhecimento = Column(String(90), nullable=False)
    data_ocorrido = Column(TIMESTAMP, nullable=False)
    url_facial_referencia = Column(String(200), nullable=True)


class Log_Resultado_Cpf(SspUsuarioBase):
    __tablename__ = "log_resultado_cpf"

    matricula = Column(String(10), primary_key=True, index=True)
    id_usuario = Column(String(50), nullable=False)
    cpf = Column(String(14), nullable=True)
    nome_criminoso = Column(String(150), nullable=True)
    id_ficha = Column(String(30), nullable=True)
    data_ocorrido = Column(TIMESTAMP, nullable=False)

class Identidade(SspCriminososBase):
    __tablename__ = "identidade"

    cpf = Column(String(14), primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    nome_mae = Column(String(150))
    nome_pai = Column(String(150))
    data_nascimento = Column(String(20), nullable=False)
    vetor_facial = Column(String(180), nullable=False)
    url_facial = Column(String(255), nullable=False)


class FichaCriminal(SspCriminososBase):
    __tablename__ = "ficha_criminal"

    id_ficha = Column(String(30), primary_key=True, index=True)
    cpf = Column(String(14), primary_key=True, index=True)
    vulgo = Column(String(100), nullable=False)


class Crime(SspCriminososBase):
    __tablename__ = "crime"

    id_crime = Column(Integer, primary_key=True, index=True)
    id_ficha = Column(String(30), nullable=False)
    nome_crime = Column(Date, nullable=False)
    artigo = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=False)
    data_ocorrencia = Column(String(20), nullable=False)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False)
    status = Column(String(20), nullable=False)

