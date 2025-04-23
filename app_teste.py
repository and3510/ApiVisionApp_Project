import pyrebase
import requests

# 📦 Configuração do Firebase
firebase_config = {
    "apiKey": "AIzaSyDstyTlH33Et40wF5h2EuX8ebGLWgIjAAk",
    "authDomain": "facecheck-e6e81.firebaseapp.com",
    "projectId": "facecheck-e6e81",
    "storageBucket": "facecheck-e6e81.firebaseapp.com",
    "messagingSenderId": "325346120140",
    "appId": "1:325346120140:web:c92a6bae081f37d2968d69",
    "measurementId": "G-FDCCHCXPR4",
    "databaseURL": "https://facecheck-e6e81.firebaseio.com"
}

# 📧 Dados do usuário (precisa existir no Firebase Auth)
email = "and.dovale@gmail.com"       
senha = "and3872#"                 

# 🌐 Endpoints da sua API FastAPI
API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/auth/firebase"
PROTECTED_ENDPOINT = f"{API_BASE}/usuario/perfil"

# 🔐 Login no Firebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

try:
    user = auth.sign_in_with_email_and_password(email, senha)
    id_token = user["idToken"]
    print("[✅] Firebase ID Token obtido com sucesso.")
except Exception as e:
    print("[❌] Erro ao fazer login no Firebase:", e)
    exit()

# 🔄 Envia o ID token para obter o token JWT da API
response = requests.post(AUTH_ENDPOINT, json={"firebase_token": id_token})

if response.status_code == 200:
    jwt_token = response.json()["access_token"]
    print("[✅] JWT da API recebido com sucesso.")
    print("Token JWT:", jwt_token)  # Adicionado para exibir o token no console

else:
    print("[❌] Erro ao autenticar na API:", response.text)
    exit()

# 🔒 Faz uma requisição para rota protegida com o token da API
headers = {"Authorization": f"Bearer {jwt_token}"}
response = requests.get(PROTECTED_ENDPOINT, headers=headers)

if response.status_code == 200:
    print("[✅] Acesso à rota protegida bem-sucedido!")
    print("Resposta:", response.json())
else:
    print("[❌] Erro ao acessar rota protegida:", response.text)


# ...existing code...

# 🔍 Buscar ficha criminal pelo CPF
cpf = "08192214303"  # Substitua pelo CPF desejado
response = requests.get(f"{API_BASE}/buscar_ficha_criminal/{cpf}", headers=headers)

if response.status_code == 200:
    print("[✅] Ficha criminal encontrada:")
    print(response.json())
else:
    print("[❌] Erro ao buscar ficha criminal:", response.text)

# ...existing code...