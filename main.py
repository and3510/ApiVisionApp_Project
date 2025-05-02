# ----------- Bibliotecas -----------


import json
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session
import shutil
import os
from uuid import uuid4
import face_recognition
from fastapi.responses import JSONResponse
import numpy as np
from config.database import CinBase, SspBase
from functions.clahe import aplicar_clahe
from functions.dependencias import get_ssp_db, get_cin_db
import config.models as models
from config.database import ssp_engine, cin_engine
from firebase_admin import credentials, auth, initialize_app
from jose import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta
from functions.auth_utils import verify_token
from functions.minio import upload_to_minio
import pytz
from enum import Enum




load_dotenv()



# Inicializar Firebase Admin
cred = credentials.Certificate("firebase_config.json")
initialize_app(cred)



# ----------- Carregar variáveis de ambiente -----------

app = FastAPI()


# ----------- Dependências -----------


ssp_db_dependency = Annotated[Session, Depends(get_ssp_db)]
cin_db_dependency = Annotated[Session, Depends(get_cin_db)]

SspBase.metadata.create_all(bind=ssp_engine)
CinBase.metadata.create_all(bind=cin_engine)


# ---------- Rotas -----------


class FirebaseToken(BaseModel):
    firebase_token: str



@app.get("/usuario/perfil", tags=["Requisição do Aplicativo"], dependencies=[Depends(verify_token)])
def perfil_usuario(
    db: cin_db_dependency,
    user_data: dict = Depends(verify_token),
):
    # Pega o id_usuario (uid) do token
    id_usuario = user_data.get("sub")

    # Busca o usuário no banco
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "nome": usuario.nome,
        "cargo": usuario.cargo,
        "matricula": usuario.matricula,
        "nivel_classe": usuario.nivel_classe
    }

@app.post("/auth/firebase", tags=["Requisição do Aplicativo"])
def auth_with_firebase(token_data: FirebaseToken):
    try:
        decoded_token = auth.verify_id_token(token_data.firebase_token)
        user_id = decoded_token["uid"]

        expire = datetime.utcnow() + timedelta(minutes=1440)
        jwt_payload = {
            "sub": user_id,
            "exp": expire
        }
        jwt_token = jwt.encode(jwt_payload, os.getenv("SECRET_KEY"), algorithm="HS256")

        return {"access_token": jwt_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=401, detail="Token Firebase inválido ou expirado")



@app.post("/buscar-similaridade-foto/", dependencies=[Depends(verify_token)], tags=["Requisição do Aplicativo"])
async def buscar_similaridade(
    db: cin_db_dependency,
    ficha_db: ssp_db_dependency,
    file: UploadFile = File(...)
):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Processar a imagem com CLAHE
    imagem = aplicar_clahe(temp_file)
    encodings = face_recognition.face_encodings(imagem, num_jitters=10, model="large")
    os.remove(temp_file)

    if not encodings:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado.")

    vetor_facial = encodings[0]
    identidades = db.query(models.Identidade).all()
    if not identidades:
        raise HTTPException(status_code=404, detail="Nenhuma identidade encontrada no banco de dados.")

    similaridades = []
    for identidade in identidades:
        vetor_facial_banco = np.array(json.loads(identidade.vetor_facial))
        distancia = np.linalg.norm(vetor_facial - vetor_facial_banco)
        similaridades.append({
            "cpf": identidade.cpf,
            "nome": identidade.nome,
            "nome_mae": identidade.nome_mae,
            "nome_pai": identidade.nome_pai,
            "data_nascimento": identidade.data_nascimento,
            "url_face": identidade.url_face,
            "distancia": distancia,
        })

    # Ordena pela menor distância
    similaridades.sort(key=lambda x: x["distancia"])
    mais_similar = similaridades[0]

    LIMIAR_CONFIANTE = 0.4
    LIMIAR_AMBÍGUO = 0.5

    # Buscar ficha criminal associada ao CPF
    cpf = mais_similar["cpf"]
    ficha_criminal = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    crimes = []
    if ficha_criminal:
        crimes = ficha_db.query(models.Crime).filter(models.Crime.id_ficha == ficha_criminal.id_ficha).all()

    ficha_criminal_info = {
        "ficha_criminal": {
            "id_ficha": ficha_criminal.id_ficha,
            "vulgo": ficha_criminal.vulgo,
            "foragido": ficha_criminal.foragido
        } if ficha_criminal else None,
        "crimes": [
            {
                "id_crime": crime.id_crime,
                "nome_crime": crime.nome_crime,
                "artigo": crime.artigo,
                "descricao": crime.descricao,
                "cidade": crime.cidade,
                "estado": crime.estado,
                "status": crime.status
            }
            for crime in crimes
        ]
    }

    # Buscar todos os alertas relacionados ao CPF
    alertas = db.query(models.Mensagens_Alerta).filter(models.Mensagens_Alerta.cpf == cpf).all()
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

    if mais_similar["distancia"] < LIMIAR_CONFIANTE:
        return JSONResponse(content={
            "status": "confiante",
            "identidade": mais_similar,
            "ficha_criminal": ficha_criminal_info,
            "alertas": alertas_formatados
        })

    elif mais_similar["distancia"] < LIMIAR_AMBÍGUO:
        segunda_mais_similar = similaridades[1] if len(similaridades) > 1 else None
        return JSONResponse(content={
            "status": "ambíguo",
            "mais_proximas": [mais_similar, segunda_mais_similar],
        })

    else:
        return JSONResponse(content={
            "status": "nenhuma similaridade forte",
        })


@app.get("/buscar-ficha-criminal/{cpf}", dependencies=[Depends(verify_token)], tags=["Requisição do Aplicativo"])
async def buscar_ficha_criminal(cpf: str, identidade_db: cin_db_dependency, ficha_db: ssp_db_dependency):
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

@app.get("/alertas/cpfs",  dependencies=[Depends(verify_token)], tags=["Requisição do Aplicativo"])
async def get_cpfs_com_alerta(db: cin_db_dependency):
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

@app.post("/create-mensagem-alerta/",  dependencies=[Depends(verify_token)], tags=["Requisição do Aplicativo"])
async def create_mensagem_alerta(
    db: cin_db_dependency,
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
    identidade = db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Identidade.")

    # Verifica se a matrícula existe na tabela Usuario
    usuario = db.query(models.Usuario).filter(models.Usuario.matricula == matricula).first()
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


# CRUD 


@app.post("/create-identidade/",  dependencies=[Depends(verify_token)], tags=["CRUD"])
async def create_identidade(
    db: cin_db_dependency,
    cpf: str,
    nome: str,
    nome_mae: str,
    nome_pai: str,
    data_nascimento: str,
    file: UploadFile = File(...)
):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Processar a imagem com CLAHE
    imagem = aplicar_clahe(temp_file)
    encodings = face_recognition.face_encodings(imagem, num_jitters=10, model="large")
    if not encodings:
        os.remove(temp_file)
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado.")

    # Fazer o upload da imagem para o MinIO
    bucket_name = "imagens"
    object_name = f"{cpf}.png"
    try:
        url = upload_to_minio(bucket_name, temp_file, object_name)
    except Exception as e:
        os.remove(temp_file)
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload para o MinIO: {str(e)}")

    # Remover o arquivo temporário
    os.remove(temp_file)

    # Reduzir o vetor facial
    vetor_facial = encodings[0]
    vetor_facial_reduzido = [round(float(x), 5) for x in vetor_facial[:]]

    # Criar o registro na tabela Identidade
    db_identidade = models.Identidade(
        cpf=cpf,
        nome=nome,
        nome_pai=nome_pai,
        nome_mae=nome_mae,
        data_nascimento=data_nascimento,
        vetor_facial=json.dumps(vetor_facial_reduzido),
        url_face=url  # Armazena a URL gerada pelo MinIO
    )
    db.add(db_identidade)
    db.commit()
    db.refresh(db_identidade)

    return {
        "cpf": db_identidade.cpf,
        "nome": db_identidade.nome,
        "nome_mae": db_identidade.nome_mae,
        "nome_pai": db_identidade.nome_pai,
        "data_nascimento": db_identidade.data_nascimento,
        "vetor_facial": vetor_facial_reduzido,
        "foto_url": db_identidade.url_face  # Retorna a URL da foto
    }


@app.post("/create-usuario/",  dependencies=[Depends(verify_token)], tags=["CRUD"])
async def create_usuario(
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

@app.put("/update-usuario/{matricula}",  dependencies=[Depends(verify_token)], tags=["CRUD"])
async def update_usuario(
    matricula: str,
    db: cin_db_dependency,
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

@app.delete("/delete-usuario/{matricula}",  dependencies=[Depends(verify_token)], tags=["CRUD"])
async def delete_usuario(matricula: str, db: cin_db_dependency):
    # Recuperar o usuário do banco de dados usando matrícula
    db_usuario = db.query(models.Usuario).filter(models.Usuario.matricula == matricula).first()

    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    try:
        # Revogar os tokens do usuário no Firebase (invalida o JWT atual)
        auth.revoke_refresh_tokens(db_usuario.id_usuario)

        # Agora sim, deletar o usuário do Firebase
        auth.delete_user(db_usuario.id_usuario)
    except auth.UserNotFoundError:
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover usuário do Firebase: {str(e)}")

    # Remover o usuário do banco de dados
    db.delete(db_usuario)
    db.commit()

    return {"message": "Usuário removido com sucesso."}



class CrimeStatus(str, Enum):
    investigando = "Em Aberto"
    condenado = "Condenado"
    cumprindo = "Cumprido"
    absolvido = "Absolvido"
    arquivado = "Arquivado"



@app.put("/update-ficha/",  dependencies=[Depends(verify_token)], tags=["CRUD"])
async def update_ficha(
    db: ssp_db_dependency,
    cpf: str,
    vulgo: str = None,
    foragido: bool = None,
):
    # Verifica se a ficha criminal existe para o CPF fornecido
    ficha_criminal = db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()
    if not ficha_criminal:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Ficha Criminal.")

    # Atualiza os campos apenas se forem fornecidos
    if vulgo is not None:
        ficha_criminal.vulgo = vulgo
    if foragido is not None:
        ficha_criminal.foragido = foragido

    # Salva as alterações no banco de dados
    db.commit()
    db.refresh(ficha_criminal)

    return {
        "message": "Ficha criminal atualizada com sucesso.",
        "ficha_criminal": {
            "id_ficha": ficha_criminal.id_ficha,
            "cpf": ficha_criminal.cpf,
            "vulgo": ficha_criminal.vulgo,
            "foragido": ficha_criminal.foragido,
        }
    }
    


@app.post("/create-crime/",  dependencies=[Depends(verify_token)], tags=["CRUD"])
async def create_crime(
    db: ssp_db_dependency,
    db1: cin_db_dependency,
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
    identidade = db1.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
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

