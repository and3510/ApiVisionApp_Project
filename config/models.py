from sqlalchemy import TIMESTAMP, Column, Date, DateTime, ForeignKey, Integer, String, Boolean, Text
from config.database import SspBase, CinBase


class Usuario(CinBase):

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

class Identidade(CinBase):
    __tablename__ = "identidade"

    cpf = Column(String(14), primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    nome_mae = Column(String(150))
    nome_pai = Column(String(150))
    data_nascimento = Column(String(20), nullable=False)
    vetor_facial = Column(String(180), nullable=False)
    url_face = Column(String(255), nullable=False)

# class Pessoa_Alerta(CinBase):
#     __tablename__ = "pessoa_alerta"

#     id_alerta = Column(String(30), primary_key=True, index=True)
#     cpf = Column(String(14), nullable=False)
#     matricula = Column(String(10), nullable=False)


# class Mensagens_Alerta(CinBase):
#     __tablename__ = "mensagem_alerta"

#     id_mensagem = Column(String(30), primary_key=True, index=True)
#     id_alerta = Column(String(30), nullable=False)
#     data_mensagem = Column(String(50), nullable=False)  
#     conteudo_mensagem = Column(String, nullable=False)
#     matricula = Column(String(20), nullable=False)
#     localizacao = Column(String(150), nullable=False)
#     cpf = Column(String(14), nullable=False)


class FichaCriminal(SspBase):
    __tablename__ = "ficha_criminal"

    id_ficha = Column(String(30), primary_key=True, index=True)
    cpf = Column(String(14), primary_key=True, index=True)
    vulgo = Column(String(100), nullable=False)
    foragido = Column(Boolean, default=False)



class Crime(SspBase):
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


class Pessoa_Alerta(SspBase):
    __tablename__ = "pessoa_alerta"

    id_alerta = Column(String(30), primary_key=True, index=True)
    cpf = Column(String(14), nullable=False)
    matricula = Column(String(10), nullable=False)


class Mensagens_Alerta(SspBase):
    __tablename__ = "mensagem_alerta"

    id_mensagem = Column(String(30), primary_key=True, index=True)
    id_alerta = Column(String(30), nullable=False)
    data_mensagem = Column(String(50), nullable=False)  
    conteudo_mensagem = Column(String, nullable=False)
    matricula = Column(String(20), nullable=False)
    localizacao = Column(String(150), nullable=False)
    cpf = Column(String(14), nullable=False)
