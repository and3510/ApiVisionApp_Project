# ----------- Bibliotecas -----------


from fastapi import FastAPI, Depends, Form, HTTPException, UploadFile, File, Security
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy import null
from sqlalchemy.orm import Session
import shutil
import os
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


# @app.get("/usuario/perfil")
# def perfil_usuario(user_data: dict = Depends(verify_token)):
#     return {"mensagem": "Bem-vindo!", "usuario": user_data.get("sub")}


@app.get("/usuario/perfil", tags=["Requisição do Aplicativo"], dependencies=[Depends(verify_token)])
def perfil_usuario(
    db: ssp_db_dependency,
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


@app.post("/create-ficha-criminal/", tags=["CRUD"])
async def create_ficha_criminal(db: ssp_db_dependency,  identidade_db: cin_db_dependency, cpf: str, ficha_criminal: str, foragido: bool = False):
    cpf_existente = identidade_db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not cpf_existente:
        raise HTTPException(status_code=400, detail="CPF não encontrado na tabela Identidade.")
    db_ficha = models.FichaCriminal(
        cpf=cpf,
        nome="Nome não informado",
        ficha_criminal=ficha_criminal,
        foragido=foragido
    )
    db.add(db_ficha)
    db.commit()
    db.refresh(db_ficha)
    return db_ficha


@app.post("/create-identidade/", tags=["CRUD"])
async def create_identidade(
    db: cin_db_dependency,
    cpf: str,
    nome: str,
    nome_mae: str,
    file: UploadFile = File(...)
):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    imagem = aplicar_clahe(temp_file)  # <--- Imagem tratada com CLAHE
    encodings = face_recognition.face_encodings(imagem)
    os.remove(temp_file)

    if not encodings:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado.")

    vetor_facial = encodings[0]
    vetor_facial_reduzido = [round(float(x), 5) for x in vetor_facial[:]]

    db_identidade = models.Identidade(
        cpf=cpf,
        nome=nome,
        nome_mae=nome_mae,
        vetor_facial=vetor_facial_reduzido
    )
    db.add(db_identidade)
    db.commit()
    db.refresh(db_identidade)

    return {
        "cpf": db_identidade.cpf,
        "nome": db_identidade.nome,
        "nome_mae": db_identidade.nome_mae,
        "vetor_facial": vetor_facial_reduzido
    }


@app.post("/buscar-similaridade-foto/", dependencies=[Depends(verify_token)], tags=["Requisição do Aplicativo"])
async def buscar_similaridade(
    db: cin_db_dependency,
    file: UploadFile = File(...)
):
    temp_file = f"temp_{file.filename}"
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    imagem = aplicar_clahe(temp_file)  # Imagem tratada com CLAHE
    encodings = face_recognition.face_encodings(imagem)
    os.remove(temp_file)

    if not encodings:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado.")

    vetor_facial = encodings[0]
    identidades = db.query(models.Identidade).all()
    if not identidades:
        raise HTTPException(status_code=404, detail="Nenhuma identidade encontrada no banco de dados.")

    similaridades = []
    for identidade in identidades:
        vetor_facial_banco = np.array(eval(identidade.vetor_facial))
        distancia = np.linalg.norm(vetor_facial - vetor_facial_banco)
        similaridades.append({
            "cpf": identidade.cpf,
            "nome": identidade.nome,
            "nome_mae": identidade.nome_mae,
            "distancia": distancia
        })

    # Ordena pela menor distância
    similaridades.sort(key=lambda x: x["distancia"])
    mais_similar = similaridades[0]

    LIMIAR_CONFIANTE = 0.3
    LIMIAR_AMBÍGUO = 0.5

    if mais_similar["distancia"] < LIMIAR_CONFIANTE:
        return JSONResponse(content={
            "status": "confiante",
            "identidade": mais_similar
        })

    elif mais_similar["distancia"] < LIMIAR_AMBÍGUO:
        segunda_mais_similar = similaridades[1] if len(similaridades) > 1 else None
        return JSONResponse(content={
            "status": "ambíguo",
            "mais_proximas": [mais_similar, segunda_mais_similar]
        })

    else:
        return JSONResponse(content={
            "status": "nenhuma similaridade forte",
            "mais_proxima": mais_similar
        })


@app.get("/buscar-ficha-criminal/{cpf}", dependencies=[Depends(verify_token)],  tags=["Requisição do Aplicativo"])
async def buscar_ficha_criminal(cpf: str, identidade_db: cin_db_dependency, ficha_db: ssp_db_dependency):
    # Verificar se o CPF existe na tabela Identidade
    identidade = identidade_db.query(models.Identidade).filter(models.Identidade.cpf == cpf).first()
    if not identidade:
        raise HTTPException(status_code=404, detail="CPF não encontrado na tabela Identidade.")

    # Verificar se o CPF possui ficha criminal
    ficha_criminal = ficha_db.query(models.FichaCriminal).filter(models.FichaCriminal.cpf == cpf).first()

    # Construir a resposta
    resposta = {
        "cpf": identidade.cpf,
        "nome": identidade.nome,
        "nome_mae": identidade.nome_mae,
    }

    if ficha_criminal:
        resposta["ficha_criminal"] = ficha_criminal.ficha_criminal
        resposta["foragido"] = ficha_criminal.foragido

    return resposta




@app.post("/create-usuario/", tags=["CRUD"])
async def create_usuario(
    db: ssp_db_dependency,
    matricula: str,
    nome: str,
    nome_mae: str,
    nome_pai: str,
    data_nascimento: str,
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
    db.commit()
    db.refresh(db_usuario)

    return db_usuario

@app.put("/update-usuario/{matricula}", tags=["CRUD"])
async def update_usuario(
    matricula: str,
    db: ssp_db_dependency,
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
    # Recuperar o usuário do banco de dados usando matricula
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

    db.commit()
    db.refresh(db_usuario)

    return db_usuario


@app.delete("/delete-usuario/{matricula}", tags=["CRUD"])
async def delete_usuario(matricula: str, db: ssp_db_dependency):
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



@app.post("/create-mensagem-alerta/", dependencies=[Depends(verify_token)], tags=["Requisição do Aplicativo"])
async def create_mensagem_alerta(
    db: cin_db_dependency,
    db1: ssp_db_dependency,
    cpf: str,
    conteudo_mensagem: str,
    matricula: str,
    localizacao: str
):
    """
    Cria uma nova mensagem de alerta. Verifica se o CPF existe na tabela Identidade
    e se a matrícula existe na tabela Usuario. Se o CPF já existir na tabela Pessoa_Alerta,
    reutiliza o id_alerta existente. Caso contrário, cria um novo registro em Pessoa_Alerta.
    """
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
    usuario = db1.query(models.Usuario).filter(models.Usuario.matricula == matricula).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada na tabela Usuario.")

    # Verifica se o CPF já existe na tabela Pessoa_Alerta
    pessoa_alerta = db.query(models.Pessoa_Alerta).filter(models.Pessoa_Alerta.cpf == cpf).first()

    if pessoa_alerta:
        # Reutiliza o id_alerta existente
        id_alerta = pessoa_alerta.id_alerta
    else:
        # Cria um novo registro em Pessoa_Alerta
        id_alerta = generate_short_uuid()  # Gera um novo ID com no máximo 20 caracteres
        nova_pessoa_alerta = models.Pessoa_Alerta(
            id_alerta=id_alerta,
            cpf=cpf,
            matricula=matricula
        )
        db.add(nova_pessoa_alerta)
        db.commit()
        db.refresh(nova_pessoa_alerta)

    # Cria um novo registro em Mensagens_Alerta
    nova_mensagem = models.Mensagens_Alerta(
        id_mensagem=generate_short_uuid(),  # Gera um novo ID com no máximo 20 caracteres
        id_alerta=id_alerta,
        data_mensagem=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Data atual
        conteudo_mensagem=conteudo_mensagem,
        matricula=matricula,
        localizacao=localizacao,
        cpf=cpf
    )
    db.add(nova_mensagem)
    db.commit()
    db.refresh(nova_mensagem)

    return nova_mensagem